package com.lifelink.dto;

import com.lifelink.model.BloodRequest;
import com.lifelink.model.User;
import lombok.Data;

@Data
public class BloodRequestDto {
    private User.BloodType bloodType;
    private BloodRequest.Urgency urgency;
    private Integer unitsNeeded;
    private String hospitalName;
    private String hospitalAddress;
    private Double latitude;
    private Double longitude;
    private String description;
    private String contactPhone;
}