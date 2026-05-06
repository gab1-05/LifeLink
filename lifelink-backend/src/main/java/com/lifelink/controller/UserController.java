package com.lifelink.controller;

import com.lifelink.model.User;
import com.lifelink.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @Autowired private UserRepository userRepo;

    @GetMapping("/me")
    public ResponseEntity<?> getMe(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        return ResponseEntity.ok(user);
    }

    @PutMapping("/me")
    public ResponseEntity<?> updateMe(@RequestBody Map<String, Object> updates,
            @AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();

        if (updates.containsKey("fullName")) user.setFullName((String) updates.get("fullName"));
        if (updates.containsKey("phone")) user.setPhone((String) updates.get("phone"));
        if (updates.containsKey("city")) user.setCity((String) updates.get("city"));
        if (updates.containsKey("bio")) user.setBio((String) updates.get("bio"));
        if (updates.containsKey("isAvailable")) user.setIsAvailable((Boolean) updates.get("isAvailable"));
        if (updates.containsKey("latitude")) user.setLatitude(((Number) updates.get("latitude")).doubleValue());
        if (updates.containsKey("longitude")) user.setLongitude(((Number) updates.get("longitude")).doubleValue());

        userRepo.save(user);
        return ResponseEntity.ok(user);
    }

    @GetMapping("/donors")
    public ResponseEntity<?> getAllDonors(
            @RequestParam(required = false) String bloodType,
            @RequestParam(required = false) Double lat,
            @RequestParam(required = false) Double lng,
            @RequestParam(defaultValue = "50") double radius) {

        if (bloodType != null && lat != null && lng != null) {
            List<User> donors = userRepo.findNearbyDonors(lat, lng, bloodType, radius);
            return ResponseEntity.ok(donors);
        }

        if (bloodType != null) {
            User.BloodType bt = User.BloodType.valueOf(bloodType);
            return ResponseEntity.ok(userRepo.findByBloodTypeAndIsAvailableTrue(bt));
        }

        List<User> all = userRepo.findAll().stream()
            .filter(u -> u.getRole() == User.UserRole.DONOR)
            .toList();
        return ResponseEntity.ok(all);
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getUser(@PathVariable Long id) {
        return userRepo.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }

    @PatchMapping("/{id}/rate")
    public ResponseEntity<?> rateUser(@PathVariable Long id,
            @RequestBody Map<String, Object> body) {
        User user = userRepo.findById(id).orElseThrow();
        double newRating = ((Number) body.get("rating")).doubleValue();
        int count = user.getRatingCount() != null ? user.getRatingCount() : 0;
        double current = user.getRating() != null ? user.getRating() : 5.0;
        user.setRating((current * count + newRating) / (count + 1));
        user.setRatingCount(count + 1);
        userRepo.save(user);
        return ResponseEntity.ok(Map.of("rating", user.getRating()));
    }

    @PatchMapping("/toggle-availability")
    public ResponseEntity<?> toggleAvailability(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        user.setIsAvailable(!Boolean.TRUE.equals(user.getIsAvailable()));
        userRepo.save(user);
        return ResponseEntity.ok(Map.of("isAvailable", user.getIsAvailable()));
    }
}