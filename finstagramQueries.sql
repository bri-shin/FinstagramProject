-- 3.1 Query to find photoIDs of photos that are visible to the user whose username

SELECT
    photoID
FROM
    Photo
JOIN Person ON(
        Photo.photoPoster = Person.username
    )
WHERE
    allFollowers = TRUE AND username IN(
    SELECT
        username_follower
    FROM
        Follow
    WHERE
        username_followed = Photo.photoPoster
) OR username IN(
    SELECT
        member_username
    FROM
        BelongTo
    NATURAL JOIN SharedWith WHERE SharedWith.photoID = Photo.photoID
)