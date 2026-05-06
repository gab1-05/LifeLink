package com.lifelink.controller;

import com.lifelink.dto.MessageDto;
import com.lifelink.model.Message;
import com.lifelink.model.User;
import com.lifelink.repository.MessageRepository;
import com.lifelink.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/messages")
public class MessageController {

    @Autowired
    private MessageRepository messageRepo;

    @Autowired
    private UserRepository userRepo;

    @Autowired(required = false)
    private SimpMessagingTemplate messagingTemplate;

    @PostMapping
    public ResponseEntity<?> sendMessage(
            @RequestBody MessageDto dto,
            @AuthenticationPrincipal UserDetails userDetails) {

        User sender = userRepo.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("Sender not found"));

        User receiver = userRepo.findById(dto.getReceiverId())
                .orElseThrow(() -> new RuntimeException("Receiver not found"));

        Message message = Message.builder()
                .sender(sender)
                .receiver(receiver)
                .content(dto.getContent())
                .bloodRequestId(dto.getBloodRequestId())
                .isRead(false)
                .build();

        messageRepo.save(message);

        if (messagingTemplate != null) {
            messagingTemplate.convertAndSendToUser(
                    receiver.getEmail(),
                    "/queue/messages",
                    Map.of(
                            "id", message.getId(),
                            "senderId", sender.getId(),
                            "senderName", sender.getFullName(),
                            "content", message.getContent(),
                            "bloodRequestId", message.getBloodRequestId()
                    )
            );
        }

        return ResponseEntity.ok(Map.of(
                "message", "Message sent successfully",
                "data", message
        ));
    }

    @GetMapping("/conversation/{userId}")
    public ResponseEntity<?> getConversation(
            @PathVariable Long userId,
            @AuthenticationPrincipal UserDetails userDetails) {

        User currentUser = userRepo.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        User otherUser = userRepo.findById(userId)
                .orElseThrow(() -> new RuntimeException("Other user not found"));

        return ResponseEntity.ok(messageRepo.findConversation(currentUser, otherUser));
    }

    @GetMapping("/inbox")
    public ResponseEntity<?> getInbox(@AuthenticationPrincipal UserDetails userDetails) {
        User currentUser = userRepo.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        return ResponseEntity.ok(messageRepo.findByReceiverOrderBySentAtDesc(currentUser));
    }

    @GetMapping("/sent")
    public ResponseEntity<?> getSent(@AuthenticationPrincipal UserDetails userDetails) {
        User currentUser = userRepo.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        return ResponseEntity.ok(messageRepo.findBySenderOrderBySentAtDesc(currentUser));
    }

    @GetMapping("/unread-count")
    public ResponseEntity<?> getUnreadCount(@AuthenticationPrincipal UserDetails userDetails) {
        User currentUser = userRepo.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        long count = messageRepo.countByReceiverAndIsReadFalse(currentUser);
        return ResponseEntity.ok(Map.of("count", count));
    }

    @PatchMapping("/{id}/read")
    public ResponseEntity<?> markAsRead(
            @PathVariable Long id,
            @AuthenticationPrincipal UserDetails userDetails) {

        User currentUser = userRepo.findByEmail(userDetails.getUsername())
                .orElseThrow(() -> new RuntimeException("User not found"));

        Message message = messageRepo.findById(id)
                .orElseThrow(() -> new RuntimeException("Message not found"));

        if (!message.getReceiver().getId().equals(currentUser.getId())) {
            return ResponseEntity.status(403).body(Map.of("error", "Not allowed"));
        }

        message.setIsRead(true);
        messageRepo.save(message);

        return ResponseEntity.ok(Map.of("message", "Message marked as read"));
    }
}