# -- User Registration
# Invalid email format
E001_INVALID_EMAIL_FORMAT = {
    "message": "Email format is incorrect.",
    "error_code": "E0010001",
}
# Email not verified
E001_EMAIL_NOT_VERIFIED = {
    "message": "User registration failed.",
    "error_code": "E0010002",
}
# Email already in use
E001_EMAIL_ALREADY_IN_USE = {
    "message": "User registration failed.",
    "error_code": "E0010003",
}
# Invalid password format
E001_INVALID_PASSWORD = {
    "message": "Password must be a combination of letters and numbers, between 6 and 30 characters long.",
    "error_code": "E0010004",
}
# Passwords do not match
E001_PASSWORD_MISMATCH = {
    "message": "Passwords do not match.",
    "error_code": "E0010005",
}

# -- Email Verification
# Invalid hashed email format
E002_INVALID_HASHED_EMAIL_FORMAT = {
    "message": "Email verification failed.",
    "error_code": "E0020001",
}
# Invalid email verification token
E002_INVALID_VERIFICATION_TOKEN = {
    "message": "Email verification failed.",
    "error_code": "E0020002",
}
# No verification information in cache
E002_VERIFICATION_INFO_NOT_FOUND = {
    "non_field": {
        "message": "Email verification failed.",
        "error_code": "E0020003",
    }
}
# Email address already verified
E002_EMAIL_ALREADY_VERIFIED = {
    "non_field": {
        "message": "Email verification failed.",
        "error_code": "E0020004",
    }
}
# Token not stored or does not match
E002_VERIFICATION_TOKEN_NOT_MATCH = {
    "non_field": {
        "message": "Email verification failed.",
        "error_code": "E0020005",
    }
}

# -- Login
# Invalid password format (Note: message implies password mismatch, not format)
E003_INVALID_PASSWORD = {
    "non_field": {
        "message": "Passwords do not match.",
        "error_code": "E0030001",
    }
}
# Email not verified
E003_EMAIL_NOT_VERIFIED = {
    "non_field": {
        "message": "Please complete email verification.",
        "error_code": "E0030002",
    }
}
# Profile must be registered to log in
E003_PROFILE_NOT_FOUND = {
    "non_field": {
        "message": "Profile is not registered.",
        "error_code": "E0030004",
    }
}
# Refresh token reissuance failed
E003_REFRESH_TOKEN_FAILED = {
    "message": "Refresh token reissuance failed.",
    "error_code": "E0030003",
}
# Token is invalid
E003_INVALID_REFRESH_TOKEN = {
    "message": "Token is invalid.",
    "error_code": "E0030005",
}
# Blacklist processing failed
E003_BLACKLIST_FAILED = {
    "message": "Blacklist processing failed.",
    "error_code": "E0030006",
}
# User not found
E003_USER_NOT_FOUND = {
    "message": "User not found.",
    "error_code": "E0030007",
}

# -- Password Reset
# Invalid hashed email format
E004_INVALID_HASHED_EMAIL_FORMAT = {
    "message": "Email verification failed.",
    "error_code": "E0040001",
}
# Invalid email verification token
E004_INVALID_VERIFICATION_TOKEN = {
    "message": "Email verification failed.",
    "error_code": "E0040002",
}
# No verification information in cache
E004_VERIFICATION_INFO_NOT_FOUND = {
    "non_field": {
        "message": "Email verification failed.",
        "error_code": "E0040003",
    }
}
# Token not stored or does not match
E004_VERIFICATION_TOKEN_NOT_MATCH = {
    "non_field": {
        "message": "Email verification failed.",
        "error_code": "E0040005",
    }
}

# -- ShortURL
# Hash value already exists
E005_HASHED_VALUE_ALREADY_EXISTS = {
    "non_field": {
        "message": "Hash value already exists.",
        "error_code": "E0050001",
    }
}
# OG tag must be in JSON format
E005_INVALID_OG_TAG_FORMAT = {
    "message": "OG tag must be in JSON format.",
    "error_code": "E0050002",
}

# -- Feed
# Feed already reported
E006_FEED_ALREADY_REPORTED = {
    "non_field": {
        "message": "Feed has already been reported.",
        "error_code": "E0060001",
    },
}
# Feed comment already reported
E006_COMMENT_ALREADY_REPORTED = {
    "non_field": {
        "message": "Feed comment has already been reported.",
        "error_code": "E0060002",
    },
}
# Feed not found
E006_FEED_NOT_FOUND = {
    "message": "Feed not found.",
    "error_code": "E0060003",
}
# Cannot change parent comment
E006_CANNOT_CHANGE_PARENT_COMMENT = {
    "message": "Cannot change parent comment.",
    "error_code": "E0060004",
}
# Parent comment not found
E006_PARENT_COMMENT_NOT_FOUND = {
    "message": "Parent comment not found.",
    "error_code": "E0060005",
}

# -- Device
# Device UUID is required for device registration
E007_DEVICE_UUID_REQUIRED = {
    "message": "Device UUID is required.",
    "error_code": "E0070001",
}
# Device already registered with my account
E007_DEVICE_ALREADY_REGISTERED = {
    "message": "Device is already registered with my account.",
    "error_code": "E0070002",
}
# Push token is required
E007_PUSH_TOKEN_REQUIRED = {
    "message": "Push token is required.",
    "error_code": "E0070003",
}
# Push token already registered
E007_PUSH_TOKEN_ALREADY_REGISTERED = {
    "message": "Push token is already registered.",
    "error_code": "E0070004",
}

# -- Profile
# Nickname length is incorrect
E008_INVALID_NICKNAME_LENGTH = {
    "message": "Nickname must be between 2 and 30 characters long.",
    "error_code": "E0080001",
}
# Leading and trailing space check
E008_INVALID_NICKNAME_SPACING = {
    "message": "Nickname cannot start or end with a space.",
    "error_code": "E0080002",
}
# Consecutive space check
E008_INVALID_NICKNAME_CONSECUTIVE_SPACES = {
    "message": "Nickname cannot contain consecutive spaces.",
    "error_code": "E0080003",
}
# Nickname regex check
E008_INVALID_NICKNAME_FORMAT = {
    "message": "Nickname can only contain Korean, English, numbers, and special characters (-_.+=^!).",
    "error_code": "E0080004",
}
# Separately defined forbidden word check
E008_NICKNAME_CONTAINS_FORBIDDEN_WORD = {
    "message": "Nickname contains forbidden words.",
    "error_code": "E0080005",
}
# Profanity check
E008_NICKNAME_CONTAINS_PROFANITY = {
    "message": "Nickname contains profanity.",
    "error_code": "E0080006",
}

# -- Agreement
# id and is_agreed fields are required for agreement consent request
E009_AGREEMENT_ID_REQUIRED = {
    "message": "id and is_agreed fields are required for agreement consent request.",
    "error_code": "E0090001",
}
# Non-existent agreement id
E009_AGREEMENT_NOT_FOUND = {
    "message": "Agreement not found.",
    "error_code": "E0090002",
}
# Required agreement not agreed to
E009_AGREEMENT_REQUIRED = {
    "message": "Required agreements must be agreed to.",
    "error_code": "E0090003",
}
# Agreement or disagreement required for all active agreements
E009_AGREEMENT_REQUIRED_ALL = {
    "message": "Agreement or disagreement is required for all active agreements.",
    "error_code": "E0090004",
}
