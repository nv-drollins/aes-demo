#!/usr/bin/env python3
import asyncio
import base64
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(__file__).resolve().parent.parent
UV = Path.home() / ".hermes" / "bin" / "uv"


def text_from(result):
    return "\n".join(item.text for item in result.content if item.type == "text")


async def main():
    server = StdioServerParameters(
        command=str(UV),
        args=["--directory", str(ROOT / "freecad-mcp"), "run", "freecad-mcp"],
    )

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            documents = await session.call_tool("list_documents", {})
            if "HermesSmokeTest" not in text_from(documents):
                await session.call_tool("create_document", {"name": "HermesSmokeTest"})

            objects = await session.call_tool(
                "get_objects", {"doc_name": "HermesSmokeTest"}
            )
            if "TestBox" not in text_from(objects):
                await session.call_tool(
                    "create_object",
                    {
                        "doc_name": "HermesSmokeTest",
                        "obj_type": "Part::Box",
                        "obj_name": "TestBox",
                        "obj_properties": {
                            "Length": 20,
                            "Width": 15,
                            "Height": 10,
                        },
                    },
                )

            box = await session.call_tool(
                "get_object",
                {"doc_name": "HermesSmokeTest", "obj_name": "TestBox"},
            )
            print(text_from(box))

            model_path = ROOT / "HermesSmokeTest.FCStd"
            await session.call_tool(
                "execute_code",
                {
                    "code": (
                        "doc = App.getDocument('HermesSmokeTest')\n"
                        "doc.recompute()\n"
                        f"doc.saveAs({str(model_path)!r})\n"
                        "print('saved', doc.FileName)"
                    )
                },
            )

            view = await session.call_tool(
                "get_view",
                {"view_name": "Isometric", "width": 800, "height": 600},
            )
            image_path = ROOT / "HermesSmokeTest.png"
            for item in view.content:
                if item.type == "image":
                    image_path.write_bytes(base64.b64decode(item.data))
                    break

            print(f"Saved model: {model_path}")
            print(f"Saved view:  {image_path}")


if __name__ == "__main__":
    asyncio.run(main())
