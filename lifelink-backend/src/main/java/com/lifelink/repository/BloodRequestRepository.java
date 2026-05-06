package com.lifelink.repository;

import com.lifelink.model.BloodRequest;
import com.lifelink.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface BloodRequestRepository extends JpaRepository<BloodRequest, Long> {

    List<BloodRequest> findByPatientOrderByCreatedAtDesc(User patient);

    List<BloodRequest> findByStatusOrderByCreatedAtDesc(BloodRequest.RequestStatus status);

    List<BloodRequest> findByBloodTypeAndStatusOrderByUrgencyDescCreatedAtDesc(
        User.BloodType bloodType, BloodRequest.RequestStatus status);

    @Query(value = """
        SELECT *, (
            6371 * acos(
                cos(radians(:lat)) * cos(radians(latitude)) *
                cos(radians(longitude) - radians(:lng)) +
                sin(radians(:lat)) * sin(radians(latitude))
            )
        ) AS distance
        FROM blood_requests
        WHERE blood_type = :bloodType
          AND status = 'OPEN'
          AND latitude IS NOT NULL
        HAVING distance < :radiusKm
        ORDER BY urgency DESC, distance ASC
    """, nativeQuery = true)
    List<BloodRequest> findNearbyRequests(
        @Param("lat") double lat,
        @Param("lng") double lng,
        @Param("bloodType") String bloodType,
        @Param("radiusKm") double radiusKm
    );

    long countByStatus(BloodRequest.RequestStatus status);

    @Query("SELECT COUNT(r) FROM BloodRequest r WHERE r.status = 'FULFILLED'")
    long countFulfilled();
}