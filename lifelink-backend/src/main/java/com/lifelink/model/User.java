package com.lifelink.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(nullable = false)
    private String password;

    @Column(nullable = false)
    private String fullName;

    private String phone;

    @Enumerated(EnumType.STRING)
    private BloodType bloodType;

    @Enumerated(EnumType.STRING)
    @Builder.Default
    private UserRole role = UserRole.DONOR;

    private Double latitude;
    private Double longitude;
    private String city;
    private String address;

    @Builder.Default
    private Boolean isAvailable = true;

    @Builder.Default
    private Boolean isVerified = false;

    private Integer totalDonations;
    private LocalDateTime lastDonationDate;
    private LocalDateTime nextEligibleDate;

    private Double rating;
    private Integer ratingCount;

    private String profileImage;
    private String bio;

    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();

    @Builder.Default
    private LocalDateTime updatedAt = LocalDateTime.now();

    @PreUpdate
    public void preUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    public enum BloodType {
        A_POSITIVE("A+"), A_NEGATIVE("A-"),
        B_POSITIVE("B+"), B_NEGATIVE("B-"),
        AB_POSITIVE("AB+"), AB_NEGATIVE("AB-"),
        O_POSITIVE("O+"), O_NEGATIVE("O-");

        private final String label;
        BloodType(String label) { this.label = label; }
        public String getLabel() { return label; }
    }

    public enum UserRole {
        DONOR, PATIENT, HOSPITAL, ADMIN
    }
}