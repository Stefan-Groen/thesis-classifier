import sqlite3
from pathlib import Path
import aiohttp
import asyncio
import json


def ensure_classification_column(DB_path):
    """ Ensure the classification_response column exists in the articles table. """
    connect = sqlite3.connect(DB_path)
    cursor = connect.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(articles)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'classification_response' not in columns:
        # Add the column if it doesn't exist
        cursor.execute("ALTER TABLE articles ADD COLUMN classification_response TEXT")
        connect.commit()
        print("Added classification_response column to articles table")
    
    connect.close()


def get_pending_entries(DB_path):
    """ Retrieve entries from the database that have the status 'PENDING' (not classified yet). """

    connect = sqlite3.connect(DB_path)
    cursor = connect.cursor()
    query = "SELECT * FROM articles WHERE status = 'PENDING'"
    cursor.execute(query)
    rows = cursor.fetchall()
    connect.close()
    return rows




async def send_to_chutes(session, title, summary, API_KEY):
    ''' Sends a single article to Chutes LLM for classification'''

    # chutes endpoint and header information
    url = "https://llm.chutes.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "user",
                "content": f"Explain why this article as threat or opportunity or neutral for JUMBO Supermarkten:\n\nTitle: {title}\n\nSummary: {summary}"
            }
        ],
        "max_tokens": 512,
        "temperature": 0.5
    }

    # HTTP request + reponse handling
    #1. sent prompt to chutes model API (url)
    #2. if server returns error, raise exception
    #3. if successful, extract the classification result from the JSON response
    #4. returns the result
    async with session.post(url, headers=headers, json=body) as response:
        response.raise_for_status()
        data = await response.json()
        # result = data["choices"][0]["message"]["content"]
        return data





def save_classification_to_db(DB_path, article_id, classification_data, status='SENT'):
    """ Save the classification response to the database and update the article status. """
    connect = sqlite3.connect(DB_path)
    cursor = connect.cursor()
    
    # Extract the classification content from the response
    classification_content = None
    if classification_data and "choices" in classification_data and len(classification_data["choices"]) > 0:
        classification_content = classification_data["choices"][0]["message"]["content"]
    
    # Store the full response as JSON, and also extract the content for easier access
    classification_json = json.dumps(classification_data) if classification_data else None
    
    # Update the article with classification response and status
    cursor.execute("""
        UPDATE articles 
        SET classification_response = ?, 
            status = ? 
        WHERE id = ?
    """, (classification_json, status, article_id))
    
    connect.commit()
    connect.close()
    
    return classification_content


async def prepare_for_LLM(pending_entries, API_KEY, DB_path):
    ''' prepares the new entries for classification and sends them one by one to LLM'''

    # Ensure the classification_response column exists
    ensure_classification_column(DB_path)
    
    # Setup http session for API calls to chutes (efficient connection reuse)
    async with aiohttp.ClientSession() as session:
        # for every pending entry, extract the relevant fields and send to chutes
        for entry in pending_entries:
            id_original_db = entry[0]
            status = entry[1]
            title = entry[2]
            link = entry[3]
            summary = entry[4]
            date_published = entry[5]
            source = entry[6]
            added_at = entry[7]

            print(f"\nProcessing Article ID: {id_original_db}")
            try:
                # Send to chutes for classification
                classification = await send_to_chutes(session, title, summary or "", API_KEY)
                
                if classification:
                    # Save classification to database
                    classification_content = save_classification_to_db(DB_path, id_original_db, classification, status='SENT')
                    print("Classification Result:")
                    print(classification_content if classification_content else "Saved but content was empty")
                    print(f"✓ Saved classification for article ID {id_original_db}")
                else:
                    # Mark as failed if no classification received
                    save_classification_to_db(DB_path, id_original_db, None, status='FAILED')
                    print(f"[WARN] id={id_original_db}: API returned an empty classification (None).")
            except Exception as e:
                # Mark as failed on error
                save_classification_to_db(DB_path, id_original_db, None, status='FAILED')
                print(f"[ERROR] id={id_original_db}: {e}")





def main():
    ''' Main function. '''

    # define the API-key and DB-path
    API_KEY = 'cpk_9d46c19845c54d5e9f6a2dcd7ef83897.8f83cfd0d5845ef885cb81164e5ae0c1.girxa5fVerpRPwdA4RXh1sYbp8RHY0RQ'
    DB_path = Path("/Users/stefan/Documents/thesis_code/rss_DB.db")

    # get_pending_entries opens the database and retrieves all entries with status 'PENDING'
    # output is a list of tuples --> [(id, status, title, link, summary, date_published, source, added_at), ...]
    pending_entries = get_pending_entries(DB_path)

    # Sent the pending entries to prepare_for_LLM function, only if there are pending entries
    if pending_entries:
        print(f'Found {len(pending_entries)} pending entries for classification.')
        asyncio.run(prepare_for_LLM(pending_entries, API_KEY, DB_path))
    else:
        print("No new entries found")


    # if pending_entries:
    #     print(f"Found {len(pending_entries)} pending entries for classification.")
    #     asyncio.run(invoke_chute(pending_entries, API_KEY))
    # else:
    #     print("No pending entries found.")

if __name__ == "__main__":
    main()
