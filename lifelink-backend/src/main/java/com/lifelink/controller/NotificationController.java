package com.lifelink.controller;

import com.lifelink.model.*;
import com.lifelink.repository.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/notifications")
public class NotificationController {

    @Autowired private NotificationRepository notifRepo;
    @Autowired private UserRepository userRepo;

    @GetMapping
    public ResponseEntity<?> getAll(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        return ResponseEntity.ok(notifRepo.findByUserOrderByCreatedAtDesc(user));
    }

    @GetMapping("/unread-count")
    public ResponseEntity<?> getUnreadCount(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        long count = notifRepo.countByUserAndIsReadFalse(user);
        return ResponseEntity.ok(Map.of("count", count));
    }

    @PatchMapping("/{id}/read")
    public ResponseEntity<?> markRead(@PathVariable Long id) {
        Notification n = notifRepo.findById(id).orElseThrow();
        n.setIsRead(true);
        notifRepo.save(n);
        return ResponseEntity.ok(Map.of("status", "read"));
    }

    @PatchMapping("/read-all")
    public ResponseEntity<?> markAllRead(@AuthenticationPrincipal UserDetails userDetails) {
        User user = userRepo.findByEmail(userDetails.getUsername()).orElseThrow();
        List<Notification> unread = notifRepo.findByUserAndIsReadFalse(user);
        unread.forEach(n -> n.setIsRead(true));
        notifRepo.saveAll(unread);
        return ResponseEntity.ok(Map.of("marked", unread.size()));
    }
}