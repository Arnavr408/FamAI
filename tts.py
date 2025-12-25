import edge_tts
import asyncio

async def main():
    tts = edge_tts.Communicate(text="The NASA AI system analyzed USB data, IPL matches are fun to watch, Dubai's weather is really hot and IBM deepblue is a fancy robot.", voice="en-US-AriaNeural")
    await tts.save("output.mp3")

asyncio.run(main())
