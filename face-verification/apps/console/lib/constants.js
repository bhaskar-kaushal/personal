// Mirror the limits enforced by apps/web/api/index.py and face_verification.gallery.
export const CAPACITY = 50;
export const MAX_ENROLL_IMAGES = 5;
export const MAX_UPLOAD_SIDE = 1280;
export const ID_PATTERN = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/;
export const ID_RULE = "Use letters, digits, “_”, “.” or “-”, starting with a letter or digit (max 128).";
