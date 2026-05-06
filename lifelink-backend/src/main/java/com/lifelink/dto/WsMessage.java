package com.lifelink.dto;

import lombok.*;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class WsMessage {
    private String type;
    private Object data;
    private Long senderId;
    private Long receiverId;
    private String senderName;
}