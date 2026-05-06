package com.lifelink.dto;

import com.lifelink.model.User;
import lombok.*;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserDto {
    private Long id;
    private String email;
    private String fullName;
    private String phone;
    private User.BloodType bloodType;
    private User.UserRole role;
    private String city;
    private Double latitude;
    private Double longitude;
    private Boolean isAvailable;
    private Integer totalDonations;
    private Double rating;
    private String profileImage;
    private String bio;
}