
- link to notion via notion api
- find ways to make it faster - try different models
- setup webscraping of urls
    - enable llm filtering of the content into a recipe format
    - enable the export in markdown of that recipe back into notion
    - enable the adding of that recipe into notion recipes
    - try to see if i can add the ingredients as well
- put in a ding to say that it registered that i said hey chef
- tell it to only speak in english

- performance improvements
    - move to local whisper model rather than api for near real-time transcription - DONE
    - reducing max_silence_sec on the VAD
    - move to gpt 3.5 turbo or a similar model for speed - DONE
    - change max tokens to be less than 500
        - work out what the tokens coming back are first
    - use streaming of the output -- this could be great - DONE
    - pre-warm the models - DELAYED - NOT A BIG ISSUE, ONLY FIRST CALL

- buy a raspberry pi and implement it on that



- find offline models to use in the event internet is poor [low priority]