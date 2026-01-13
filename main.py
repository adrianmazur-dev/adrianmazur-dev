import os
import sys

from dotenv import load_dotenv

from src import gen_anim, gen_profile, gen_stats


def run():
    load_dotenv()
    github_token = os.getenv("GITHUB_TOKEN")
    github_username = os.getenv("GITHUB_USERNAME")

    if not github_token:
        print("WARN: GITHUB_TOKEN environment variable is not set.")

    if not github_username:
        print("ERROR: GITHUB_USERNAME environment variable is not set.")
        sys.exit(1)

    try:
        print(f"Fetching statistics for {github_username}...")
        stats = gen_stats.get_github_stats(github_username, github_token)

        print("Generating ASCII slideshow from resources...")
        ascii_frames = gen_anim.generate_ascii_slideshow(
            "resources", new_width=50, charset="detailed", contrast=1.8, brightness=1.1
        )

        gen_profile.generate_svg("dark", stats, ascii_frames)
        gen_profile.generate_svg("light", stats, ascii_frames)
        print("\nSuccess: Profile statistics updated successfully.")
    except Exception as e:
        print(f"\nERROR: An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
