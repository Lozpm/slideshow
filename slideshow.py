#!/usr/bin/env python3
"""
Fullscreen random photo slideshow for Raspberry Pi.

Shows each photo in the folder exactly once, in random order, then
reshuffles and loops. Photos slide in from the right while the previous
one slides out to the left. Press Escape or Ctrl+C to quit.
"""

import os
import random
import sys
import pygame
from PIL import Image, ImageOps

# ---- Configuration -------------------------------------------------

PHOTO_DIR = "/home/loz/slideshow/photos"   # folder containing your photos
SECONDS_PER_PHOTO = 6                      # how long each photo is held (excludes transition)
TRANSITION_MS = 500                        # duration of the slide transition
VALID_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif")
BACKGROUND_COLOR = (0, 0, 0)               # letterbox/pillarbox colour

# ---------------------------------------------------------------------


def load_photo_list(folder):
    if not os.path.isdir(folder):
        sys.exit(f"Photo folder not found: {folder}")

    photos = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(VALID_EXTENSIONS)
    ]

    if not photos:
        sys.exit(f"No photos found in {folder}")

    return photos


def scale_to_fit(image, screen_size):
    """Scale image to fit within screen_size, preserving aspect ratio."""
    img_w, img_h = image.get_size()
    screen_w, screen_h = screen_size

    scale = min(screen_w / img_w, screen_h / img_h)
    new_size = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))

    return pygame.transform.smoothscale(image, new_size)


def render_frame(path, screen_size):
    """Load a photo and return a full-screen surface with it centred/letterboxed.

    Loaded via Pillow rather than pygame.image.load() so that EXIF orientation
    metadata is honoured -- otherwise portrait phone photos (stored as landscape
    pixel data with a rotation flag) come out sideways.
    """
    try:
        with Image.open(path) as pil_image:
            pil_image = ImageOps.exif_transpose(pil_image)  # apply EXIF rotation
            pil_image = pil_image.convert("RGB")
            data = pil_image.tobytes()
            size = pil_image.size
            image = pygame.image.fromstring(data, size, "RGB")
    except (pygame.error, OSError) as e:
        print(f"Skipping {path}: {e}")
        return None

    scaled = scale_to_fit(image, screen_size)
    screen_w, screen_h = screen_size
    img_w, img_h = scaled.get_size()

    frame = pygame.Surface(screen_size)
    frame.fill(BACKGROUND_COLOR)
    frame.blit(scaled, ((screen_w - img_w) // 2, (screen_h - img_h) // 2))

    return frame


def check_quit_events():
    """Returns False if a quit/escape event was seen, True otherwise."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False
    return True


def slide_transition(screen, old_frame, new_frame, screen_size, clock):
    """Slide new_frame in from the right while old_frame exits to the left.
    Returns False if the user requested quit during the animation."""
    screen_w, screen_h = screen_size
    elapsed = 0

    while elapsed < TRANSITION_MS:
        if not check_quit_events():
            return False

        progress = min(1.0, elapsed / TRANSITION_MS)
        # ease-out for a smoother finish
        eased = 1 - (1 - progress) ** 2
        offset = int(eased * screen_w)

        screen.fill(BACKGROUND_COLOR)
        screen.blit(old_frame, (-offset, 0))
        screen.blit(new_frame, (screen_w - offset, 0))
        pygame.display.flip()

        elapsed += clock.tick(60)

    screen.blit(new_frame, (0, 0))
    pygame.display.flip()
    return True


def hold(clock, duration_ms):
    """Wait for duration_ms while still responding to quit events."""
    elapsed = 0
    while elapsed < duration_ms:
        if not check_quit_events():
            return False
        elapsed += clock.tick(30)
    return True


def main():
    photos = load_photo_list(PHOTO_DIR)

    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_size = screen.get_size()

    clock = pygame.time.Clock()
    prev_frame = None

    try:
        while True:
            random.shuffle(photos)

            for path in photos:
                frame = render_frame(path, screen_size)
                if frame is None:
                    continue

                if prev_frame is None:
                    screen.blit(frame, (0, 0))
                    pygame.display.flip()
                else:
                    if not slide_transition(screen, prev_frame, frame, screen_size, clock):
                        return

                if not hold(clock, SECONDS_PER_PHOTO * 1000):
                    return

                prev_frame = frame

    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
