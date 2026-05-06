package com.lifelink.repository;

import com.lifelink.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    List<User> findByBloodTypeAndIsAvailableTrue(User.BloodType bloodType);

    @Query(value = """
        SELECT *, (
            6371 * acos(
                cos(radians(:lat)) * cos(radians(latitude)) *
                cos(radians(longitude) - radians(:lng)) +
                sin(radians(:lat)) * sin(radians(latitude))
            )
        ) AS distance
        FROM users
        WHERE blood_type = :bloodType
          AND is_available = true
          AND role = 'DONOR'
          AND latitude IS NOT NULL
          AND longitude IS NOT NULL
        HAVING distance < :radiusKm
        ORDER BY distance ASC
        LIMIT 50
        """, nativeQuery = true)
    List<User> findNearbyDonors(
            @Param("lat") double lat,
            @Param("lng") double lng,
            @Param("bloodType") String bloodType,
            @Param("radiusKm") double radiusKm
    );

    @Query("SELECT COUNT(u) FROM User u WHERE u.role = 'DONOR'")
    long countDonors();

    @Query("SELECT COUNT(u) FROM User u WHERE u.isAvailable = true AND u.role = 'DONOR'")
    long countAvailableDonors();
}