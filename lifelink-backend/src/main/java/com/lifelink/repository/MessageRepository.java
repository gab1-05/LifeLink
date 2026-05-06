package com.lifelink.repository;

import com.lifelink.model.Message;
import com.lifelink.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MessageRepository extends JpaRepository<Message, Long> {

    List<Message> findByReceiverOrderBySentAtDesc(User receiver);

    List<Message> findBySenderOrderBySentAtDesc(User sender);

    @Query("""
        SELECT m FROM Message m
        WHERE (m.sender = ?1 AND m.receiver = ?2)
           OR (m.sender = ?2 AND m.receiver = ?1)
        ORDER BY m.sentAt ASC
        """)
    List<Message> findConversation(User user1, User user2);

    long countByReceiverAndIsReadFalse(User receiver);
}