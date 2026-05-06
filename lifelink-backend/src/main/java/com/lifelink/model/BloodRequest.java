package com.lifelink.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "blood_requests")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BloodRequest {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "patient_id", nullable = false)
    private User patient;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private User.BloodType bloodType;

    @Enumerated(EnumType.STRING)
    @Builder.Default
    private Urgency urgency = Urgency.NORMAL;

    @Enumerated(EnumType.STRING)
    @Builder.Default
    private RequestStatus status = RequestStatus.OPEN;

    private Integer unitsNeeded;
    private String hospitalName;
    private String hospitalAddress;
    private Double latitude;
    private Double longitude;

    @Column(length = 1000)
    private String description;

    private String contactPhone;

    @Builder.Default
    private LocalDateTime createdAt = LocalDateTime.now();
    private LocalDateTime fulfilledAt;
    private LocalDateTime expiresAt;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "matched_donor_id")
    private User matchedDonor;

    public enum Urgency {
        CRITICAL, URGENT, NORMAL
    }

    public enum RequestStatus {
        OPEN, MATCHED, FULFILLED, CANCELLED, EXPIRED
    }
}