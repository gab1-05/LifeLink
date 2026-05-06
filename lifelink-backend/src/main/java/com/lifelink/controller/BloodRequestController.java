package com.lifelink.controller;

import com.lifelink.dto.BloodRequestDto;
import com.lifelink.model.*;
import com.lifelink.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.*;

@RestController
@RequestMapping("/api/requests")
public class BloodRequestController {

    @Autowired private BloodRequestRepository requestRepo;
    @Autowired private UserRepository userRepo;
    @Autowired private NotificationRepository notifRepo;
    @Autowired private SimpMessagingTemplate messagingTemplate;

    @PostMapping
    public ResponseEntity<?> createRequest(
            @RequestBody BloodRequestDto dto,
            @AuthenticationPrincipal UserDetails userDetails) {

        User patient = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();

        BloodRequest req = BloodRequest.builder()
            .patient(patient)
            .bloodType(dto.getBloodType())
            .urgency(dto.getUrgency() != null ? dto.getUrgency() : BloodRequest.Urgency.NORMAL)
            .unitsNeeded(dto.getUnitsNeeded())
            .hospitalName(dto.getHospitalName())
            .hospitalAddress(dto.getHospitalAddress())
            .latitude(dto.getLatitude())
            .longitude(dto.getLongitude())
            .description(dto.getDescription())
            .contactPhone(dto.getContactPhone())
            .status(BloodRequest.RequestStatus.OPEN)
            .expiresAt(LocalDateTime.now().plusHours(24))
            .build();

        requestRepo.save(req);

        // Notify nearby donors via WebSocket
        notifyNearbyDonors(req);

        return ResponseEntity.ok(Map.of(
            "request", req,
            "message", "Blood request posted successfully! Notifying nearby donors..."
        ));
    }

    @GetMapping
    public ResponseEntity<?> getAllOpenRequests() {
        var requests = requestRepo.findByStatusOrderByCreatedAtDesc(BloodRequest.RequestStatus.OPEN);
        return ResponseEntity.ok(requests);
    }

    @GetMapping("/my")
    public ResponseEntity<?> getMyRequests(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        return ResponseEntity.ok(requestRepo.findByPatientOrderByCreatedAtDesc(user));
    }

    @GetMapping("/nearby")
    public ResponseEntity<?> getNearbyRequests(
            @RequestParam double lat,
            @RequestParam double lng,
            @RequestParam(defaultValue = "50") double radius,
            @AuthenticationPrincipal UserDetails userDetails) {

        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        String bloodType = user.getBloodType() != null ? user.getBloodType().name() : null;

        List<BloodRequest> requests = bloodType != null
            ? requestRepo.findNearbyRequests(lat, lng, bloodType, radius)
            : requestRepo.findByStatusOrderByCreatedAtDesc(BloodRequest.RequestStatus.OPEN);

        return ResponseEntity.ok(requests);
    }

    @PatchMapping("/{id}/respond")
    public ResponseEntity<?> respondToRequest(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {

        User donor = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        BloodRequest request = requestRepo.findById(id)
            .orElseThrow(() -> new RuntimeException("Request not found"));

        request.setMatchedDonor(donor);
        request.setStatus(BloodRequest.RequestStatus.MATCHED);
        requestRepo.save(request);

        // Notify patient
        Notification notif = Notification.builder()
            .user(request.getPatient())
            .title("🩸 Donor Found!")
            .message(donor.getFullName() + " has responded to your blood request!")
            .type(Notification.NotificationType.MATCH_FOUND)
            .referenceId(request.getId())
            .build();
        notifRepo.save(notif);

        messagingTemplate.convertAndSendToUser(
            request.getPatient().getEmail(),
            "/queue/notifications",
            Map.of("type", "MATCH_FOUND", "message", notif.getMessage(), "donorName", donor.getFullName())
        );

        return ResponseEntity.ok(Map.of("message", "You've responded to the request! Contact the patient soon."));
    }

    @PatchMapping("/{id}/fulfill")
    public ResponseEntity<?> fulfillRequest(@PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {
        BloodRequest request = requestRepo.findById(id).orElseThrow();
        request.setStatus(BloodRequest.RequestStatus.FULFILLED);
        request.setFulfilledAt(LocalDateTime.now());
        requestRepo.save(request);

        if (request.getMatchedDonor() != null) {
            User donor = request.getMatchedDonor();
            donor.setTotalDonations(donor.getTotalDonations() != null ? donor.getTotalDonations() + 1 : 1);
            donor.setLastDonationDate(LocalDateTime.now());
            donor.setNextEligibleDate(LocalDateTime.now().plusDays(90));
            donor.setIsAvailable(false);
            userRepo.save(donor);
        }

        return ResponseEntity.ok(Map.of("message", "Request marked as fulfilled. Thank you! 🙏"));
    }

    @GetMapping("/stats")
    public ResponseEntity<?> getStats() {
        return ResponseEntity.ok(Map.of(
            "totalDonors", userRepo.countDonors(),
            "availableDonors", userRepo.countAvailableDonors(),
            "openRequests", requestRepo.countByStatus(BloodRequest.RequestStatus.OPEN),
            "fulfilledRequests", requestRepo.countFulfilled()
        ));
    }

    private void notifyNearbyDonors(BloodRequest req) {
        if (req.getLatitude() == null || req.getLongitude() == null) return;

        List<User> nearbyDonors = userRepo.findNearbyDonors(
            req.getLatitude(), req.getLongitude(), req.getBloodType().name(), 50);

        for (User donor : nearbyDonors) {
            Notification notif = Notification.builder()
                .user(donor)
                .title("🆘 Urgent Blood Request Nearby!")
                .message(req.getUrgency().name() + " request for " +
                    req.getBloodType().getLabel() + " blood near " + req.getHospitalName())
                .type(Notification.NotificationType.BLOOD_REQUEST)
                .referenceId(req.getId())
                .build();
            notifRepo.save(notif);

            messagingTemplate.convertAndSendToUser(
                donor.getEmail(),
                "/queue/notifications",
                Map.of("type", "BLOOD_REQUEST", "requestId", req.getId(),
                    "urgency", req.getUrgency(), "bloodType", req.getBloodType().getLabel())
            );
        }
    }
}