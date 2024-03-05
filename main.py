import google.generativeai as genai
import praw
import time
import streamlit as st
import os
from playwright.async_api import async_playwright
import asyncio
import json

async def save_session_to_json(url):

    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False,channel="firefox")
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url)
        st.info("Press Enter on the Console/CMD After Login is Complete.")
        input("Press Enter After Login is Complete.")
        session_cookies = await context.cookies()
        output_file = f'assets/session.json'
        with open(output_file, 'w') as json_file:
            json.dump(session_cookies, json_file, indent=2)
        st.info("Login Saved for the Account.")
        await browser.close()

CLIENT_ID = ""
CLIENT_SECRET = ""
CLIENT_NAME = ""

def read_data_from_file(filename):
    with open(filename, 'r') as file:
        for line in file:
            data = line.strip().split(',')
            if len(data) >= 4:
                variable1 = data[0].strip()
                variable2 = data[1].strip()
                variable3 = data[2].strip()
                variable4 = data[2].strip()
            else:
                print("Invalid data format in line:", line)
    
    return variable1, variable2, variable3, variable4

async def comment_on_post_playwright(url, comment):
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True, channel="firefox")
        context = await browser.new_context()

        cookies_file = f'assets/session.json'
        with open(cookies_file, 'r') as json_file:
                saved_cookies = json.load(json_file)
        await context.add_cookies(saved_cookies)
        
        page = await context.new_page()
        await page.goto(url)
        await asyncio.sleep(5)
        await page.click('shreddit-async-loader[bundlename="comment_composer"]')

        await asyncio.sleep(2)
        await page.keyboard.type(comment)
        await asyncio.sleep(2)
        await page.click('span[slot="content"][style="opacity: 1;"]')
        await asyncio.sleep(4)
        
def get_latest_hot_post_url(subreddit_names):
    reddit = praw.Reddit(client_id=CLIENT_ID,
                         client_secret=CLIENT_SECRET,
                         user_agent=CLIENT_NAME)

    latest_urls = []
    latest_url_titles = []

    for subreddit_name in subreddit_names:
        subreddit = reddit.subreddit(subreddit_name)
        hot_posts = subreddit.hot(limit=2)

        for post in hot_posts:
            if not post.stickied:
                latest_url = f"https://www.reddit.com{post.permalink}"
                latest_urls.append(latest_url)
                latest_url_title = post.title
                latest_url_titles.append(latest_url_title)
                break

    return latest_urls, latest_url_titles

def comment(comment_text, prompt):

    genai.configure(api_key='')
    model = genai.GenerativeModel('models/gemini-pro')
    chat = model.start_chat()
    response = chat.send_message(f'{prompt} :{comment_text}')
    return response.text


if __name__ == "__main__":

    st.set_page_config(
    page_title="Reddit Bot",
    page_icon="🤠",
    )

    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
    st.markdown('<style> .stDeployButton { display: none; } </style>', unsafe_allow_html=True)

    st.title("Reddit Commenting Bot.")
    st.divider()

    st.subheader("Sign in to Reddit")

    if st.button("Sign In"):

        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
        title=loop.run_until_complete(save_session_to_json("https://www.reddit.com/"))

    if st.button("Delete Account"):
        os.remove("assets\session.json")
        st.success("Account Removed.")

    st.divider()
    st.subheader("Enter Prompt")
    prompt = st.text_area("Enter Prompt", placeholder="Example Prompt \"This is the Title of a post, Reply to it as if you were commenting on the post, the reply should be casual, funny and short\"")
    
    st.divider()
    st.subheader("Enter Subreddits and Run")
    subreddits_list = []
    subreddits_list_count = st.number_input("How Many Subreddits Do you want to Enter", step=1, min_value=1)

    for i in range(subreddits_list_count):
        subreddits_list_item = st.text_input(f"Subreddit {i+1}.", placeholder="dankmemes", key=f'subreddits_list_item_{i}')
        subreddits_list.append(subreddits_list_item)

    if st.button("Run", type="primary"):
        with st.spinner("Running"):

            hot_posts_list, hot_posts_titles = get_latest_hot_post_url(subreddits_list)
            already_commented = []
            while True:

                for i in range(len(hot_posts_list)):

                    try:

                        if hot_posts_list[i] in already_commented:
                            st.info(f"Already Commented on Post: {hot_posts_list[i]} with Title {hot_posts_titles[i]}\n")
                        else:
                            comment_text = comment(hot_posts_titles[i], prompt)
                            st.success(f"Commenting :{comment_text} on Post\n")
                            loop = asyncio.ProactorEventLoop()
                            asyncio.set_event_loop(loop)
                            title=loop.run_until_complete(comment_on_post_playwright(hot_posts_list[i], comment_text))
                            st.success(f"Commented :{comment_text} on Post: {hot_posts_list[i]}\n")
                            already_commented.append(hot_posts_list[i])

                    except Exception as e:
                        print(e)
                    
                    time.sleep(30)

                st.info("Waiting for 2 Hour Before Check for new Hot Posts Again.")
                time.sleep(7200)