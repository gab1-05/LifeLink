package com.lifelink.dto;

import com.lifelink.model.User;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class RegisterRequest {

    @NotBlank
    private String fullName;

    @Email
    @NotBlank
    private String email;

    @NotBlank
    private String password;

    private String phone;
    private User.BloodType bloodType;
    private User.UserRole role;
    private String city;
    private Double latitude;
    private Double longitude;
}