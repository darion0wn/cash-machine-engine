from .client import RedditClient


def main():

    client = RedditClient()

    posts = client.fetch_subreddit(
        "SaaS",
        limit=10,
    )

    print(f"Found {len(posts)} posts\n")

    for post in posts:
        print("-" * 80)
        print(post.title)
        print(f"↑ {post.score} | 💬 {post.num_comments}")
        print(post.url)


if __name__ == "__main__":
    main()