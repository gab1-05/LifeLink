package com.lifelink;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class LifeLinkApplication {
    public static void main(String[] args) {
        SpringApplication.run(LifeLinkApplication.class, args);
        System.out.println("\n╔══════════════════════════════════════╗");
        System.out.println("║   🩸 LifeLink Backend Started!        ║");
        System.out.println("║   API: http://localhost:8080/api     ║");
        System.out.println("║   WS:  ws://localhost:8080/ws        ║");
        System.out.println("╚══════════════════════════════════════╝\n");
    }
}