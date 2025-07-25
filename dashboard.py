import os
import sys
import feedparser
try:
    import openai
except ImportError:
    openai = None

NUM_ROUNDS = 3

BULL_SYSTEM_PROMPT = (
    'You are a financial analyst who is bullish on {commodity}. Based on the '
    'following news items, make your argument that the price will go up.'
)
BEAR_SYSTEM_PROMPT = (
    'You are a financial analyst who is bearish on {commodity}. Based on the '
    'following news items, argue that the price will go down.'
)


def fetch_news(commodity, max_items=5):
    url = f'https://news.google.com/rss/search?q={commodity}'
    feed = feedparser.parse(url)
    items = [f"- {entry.title}" for entry in feed.entries[:max_items]]
    return '\n'.join(items)


def chat(messages):
    if openai is None:
        raise RuntimeError('openai package not installed')
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY environment variable not set')
    openai.api_key = api_key
    response = openai.chat.completions.create(
        model='gpt-3.5-turbo',
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def main(commodity):
    news_summary = fetch_news(commodity)
    bull_messages = [
        {'role': 'system', 'content': BULL_SYSTEM_PROMPT.format(commodity=commodity) + '\n' + news_summary},
    ]
    bear_messages = [
        {'role': 'system', 'content': BEAR_SYSTEM_PROMPT.format(commodity=commodity) + '\n' + news_summary},
    ]

    for round_idx in range(NUM_ROUNDS):
        bull_reply = chat(bull_messages)
        bull_messages.append({'role': 'assistant', 'content': bull_reply})
        bear_messages.append({'role': 'user', 'content': bull_reply})

        bear_reply = chat(bear_messages)
        bear_messages.append({'role': 'assistant', 'content': bear_reply})
        bull_messages.append({'role': 'user', 'content': bear_reply})

        print(f"Round {round_idx + 1} Bullish Analyst:\n{bull_reply}\n")
        print(f"Round {round_idx + 1} Bearish Analyst:\n{bear_reply}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python dashboard.py <commodity>')
        sys.exit(1)
    main(sys.argv[1])
