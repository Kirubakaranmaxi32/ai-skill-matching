# Phase 3: Student Profiles & Skills API Specification

**Project:** AI Skill Matching  
**Phase:** Phase 3 Step 4 (Backend APIs)  
**Base URL:** `/api/v1`

---

## 1. Authentication
All `/students/me/*` endpoints require an `Authorization` header containing a valid Supabase JWT token:
```http
Authorization: Bearer <SUPABASE_JWT_TOKEN>
```
Unauthenticated requests will receive `401 Unauthorized`.
All student actions resolve the student identity internally from the authenticated `auth.users(id)` (`user_id`). The client cannot spoof or override `user_id` in request payloads.

---

## 2. Reference Data Endpoints

### `GET /api/v1/departments`
- **Description:** Retrieve the list of all academic departments.
- **Auth:** Public / Optional
- **Response (200 OK):**
```json
[
  {
    "id": "d1000000-0000-0000-0000-000000000001",
    "name": "Computer Science & Engineering",
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

### `GET /api/v1/skills`
- **Description:** Retrieve the canonical skill taxonomy.
- **Auth:** Public / Optional
- **Response (200 OK):**
```json
[
  {
    "id": "a1000000-0000-0000-0000-000000000001",
    "name": "Python",
    "category": "ai_ml",
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

### `GET /api/v1/interests`
- **Description:** Retrieve available project interest domains.
- **Auth:** Public / Optional
- **Response (200 OK):**
```json
[
  {
    "id": "b1000000-0000-0000-0000-000000000001",
    "name": "Artificial Intelligence & Deep Learning",
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

---

## 3. Student Profile Endpoints

### `GET /api/v1/students/me`
- **Description:** Retrieve the authenticated student's profile. If not previously created, a default profile is automatically initialized.
- **Auth:** Required
- **Response (200 OK):**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "full_name": "Student User",
  "department_id": null,
  "academic_year": 1,
  "bio": null,
  "github_url": null,
  "linkedin_url": null,
  "portfolio_url": null,
  "hours_per_week": 10,
  "created_at": "2026-10-02T12:00:00Z",
  "updated_at": "2026-10-02T12:00:00Z"
}
```

### `PUT /api/v1/students/me`
- **Description:** Update the authenticated student's profile details.
- **Auth:** Required
- **Request Body:**
```json
{
  "full_name": "Kirubakaran S",
  "department_id": "d1000000-0000-0000-0000-000000000001",
  "academic_year": 3,
  "bio": "Passionate about Deep Learning and Full-Stack Engineering.",
  "github_url": "https://github.com/kiruba",
  "linkedin_url": "https://linkedin.com/in/kiruba",
  "portfolio_url": "https://kiruba.dev",
  "hours_per_week": 15
}
```
- **Response (200 OK):** Updated student profile object.

---

## 4. Student Skills Endpoints

### `GET /api/v1/students/me/skills`
- **Description:** List all skills associated with the authenticated student.
- **Auth:** Required
- **Response (200 OK):**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "skill_id": "a1000000-0000-0000-0000-000000000001",
    "proficiency": 3,
    "created_at": "2026-10-02T12:00:00Z",
    "skill_name": "Python",
    "category": "ai_ml"
  }
]
```

### `POST /api/v1/students/me/skills`
- **Description:** Add or update a proficiency rating for a skill (1 to 4).
- **Auth:** Required
- **Request Body:**
```json
{
  "skill_id": "a1000000-0000-0000-0000-000000000001",
  "proficiency": 3
}
```
- **Response (201 Created):** Created/updated student skill object.

### `DELETE /api/v1/students/me/skills/{skill_id}`
- **Description:** Remove a skill from the authenticated student's profile.
- **Auth:** Required
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Skill removed successfully"
}
```

---

## 5. Student Interests Endpoints

### `GET /api/v1/students/me/interests`
- **Description:** List all project interests selected by the student.
- **Auth:** Required
- **Response (200 OK):**
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "student_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "interest_id": "b1000000-0000-0000-0000-000000000001",
    "created_at": "2026-10-02T12:00:00Z",
    "interest_name": "Artificial Intelligence & Deep Learning"
  }
]
```

### `POST /api/v1/students/me/interests`
- **Description:** Map a project interest to the authenticated student.
- **Auth:** Required
- **Request Body:**
```json
{
  "interest_id": "b1000000-0000-0000-0000-000000000001"
}
```
- **Response (201 Created):** Created student interest mapping.

### `DELETE /api/v1/students/me/interests/{interest_id}`
- **Description:** Remove a project interest from the authenticated student.
- **Auth:** Required
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Interest removed successfully"
}
```

---

## 6. Certifications Endpoints

### `GET /api/v1/students/me/certifications`
- **Description:** Retrieve all certifications belonging to the student.
- **Auth:** Required
- **Response (200 OK):** List of certification records.

### `POST /api/v1/students/me/certifications`
- **Description:** Add a new certification.
- **Auth:** Required
- **Request Body:**
```json
{
  "name": "AWS Certified Cloud Practitioner",
  "issuing_organization": "Amazon Web Services",
  "issue_date": "2026-05-15",
  "credential_url": "https://aws.amazon.com/verify/12345"
}
```
- **Response (201 Created):** Created certification record with assigned ID.

### `DELETE /api/v1/students/me/certifications/{certification_id}`
- **Description:** Delete a certification (strict ownership verification).
- **Auth:** Required
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Certification deleted successfully"
}
```

---

## 7. Previous Projects Endpoints

### `GET /api/v1/students/me/projects`
- **Description:** Retrieve previous projects / portfolio items for the student.
- **Auth:** Required
- **Response (200 OK):** List of previous project records.

### `POST /api/v1/students/me/projects`
- **Description:** Add a previous project to portfolio.
- **Auth:** Required
- **Request Body:**
```json
{
  "title": "Autonomous Drone Path Planner",
  "description": "Implemented A* path search with ROS2 and OpenCV.",
  "technologies": ["Python", "OpenCV", "ROS2"],
  "project_url": "https://github.com/student/drone-planner"
}
```
- **Response (201 Created):** Created project record with assigned ID.

### `DELETE /api/v1/students/me/projects/{project_id}`
- **Description:** Delete a previous project (strict ownership verification).
- **Auth:** Required
- **Response (200 OK):**
```json
{
  "status": "success",
  "message": "Previous project deleted successfully"
}
```
