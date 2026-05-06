package com.lifelink.controller;

import com.lifelink.dto.*;
import com.lifelink.model.User;
import com.lifelink.repository.UserRepository;
import com.lifelink.security.JwtUtil;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.*;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired private AuthenticationManager authManager;
    @Autowired private UserDetailsService userDetailsService;
    @Autowired private JwtUtil jwtUtil;
    @Autowired private UserRepository userRepo;
    @Autowired private PasswordEncoder encoder;

    @PostMapping("/register")
    public ResponseEntity<?> register(@Valid @RequestBody RegisterRequest req) {
        if (userRepo.existsByEmail(req.getEmail())) {
            return ResponseEntity.badRequest().body(Map.of("error", "Email already registered"));
        }

        User user = User.builder()
            .email(req.getEmail())
            .password(encoder.encode(req.getPassword()))
            .fullName(req.getFullName())
            .phone(req.getPhone())
            .bloodType(req.getBloodType())
            .role(req.getRole() != null ? req.getRole() : User.UserRole.DONOR)
            .city(req.getCity())
            .latitude(req.getLatitude())
            .longitude(req.getLongitude())
            .isAvailable(true)
            .totalDonations(0)
            .rating(5.0)
            .ratingCount(0)
            .build();

        userRepo.save(user);

        UserDetails userDetails = userDetailsService.loadUserByUsername(user.getEmail());
        String token = jwtUtil.generateToken(userDetails);

        return ResponseEntity.ok(Map.of(
            "token", token,
            "user", toDto(user),
            "message", "Registration successful! Welcome to LifeLink 🩸"
        ));
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest req) {
        try {
            authManager.authenticate(
                new UsernamePasswordAuthenticationToken(req.getEmail(), req.getPassword()));
        } catch (BadCredentialsException e) {
            return ResponseEntity.status(401).body(Map.of("error", "Invalid credentials"));
        }

        UserDetails userDetails = userDetailsService.loadUserByUsername(req.getEmail());
        String token = jwtUtil.generateToken(userDetails);
        User user = userRepo.findByEmail(req.getEmail()).orElseThrow();

        return ResponseEntity.ok(Map.of(
            "token", token,
            "user", toDto(user)
        ));
    }

    private UserDto toDto(User u) {
        return new UserDto(u.getId(), u.getEmail(), u.getFullName(), u.getPhone(),
            u.getBloodType(), u.getRole(), u.getCity(), u.getLatitude(), u.getLongitude(),
            u.getIsAvailable(), u.getTotalDonations(), u.getRating(), u.getProfileImage(), u.getBio());
    }
}