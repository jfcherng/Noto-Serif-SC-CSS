import aiohttp
import asyncio
import os
import re
import requests

from typing import Iterable, List, Match, Optional
from urllib.parse import urlparse

# config file
from download_config import FONT_TYPE, FONT_LANG, FONT_STYLES

FONT_TYPE_LOWER = FONT_TYPE.lower()
FONT_LANG_LOWER = FONT_LANG.lower()

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

CSS_URL_PTN = "https://fonts.googleapis.com/css2?family=Noto+{font_type}+{font_lang}:wght@{font_weight}&display=swap"
RE_URL = re.compile(r"https?://[a-z0-9@~_+\-*/&=#%|:.,!?]+(?<=[a-z0-9@~_+\-*/&=#%|])", re.IGNORECASE)

REQUESTS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
}


def get_filename_from_url(url: str) -> str:
    return os.path.basename(urlparse(url).path)


def replace_url_to_local(m: Match) -> str:
    return get_filename_from_url(m.group(0))


async def download_font_parts(urls: Iterable[str], save_ptn: Optional[str] = None) -> None:
    async def get(url: str, save_ptn: Optional[str] = None) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url) as response:
                    resp = await response.read()
                    print("Got url {} with response of length {}.".format(url, len(resp)))

                    if save_ptn:
                        filename = get_filename_from_url(url)
                        with open(save_ptn.format_map({"filename": filename}), "wb") as f:
                            f.write(resp)
        except Exception as e:
            print("Unable to get url {} due to {}.".format(url, e.__class__))

    ret = await asyncio.gather(*[get(url, save_ptn) for url in urls])
    print("Finalized all. ret is a list of {} outputs.".format(len(ret)))


for font_style, font_weight in FONT_STYLES.items():
    output_dir = os.path.join(
        SCRIPT_DIR,
        "build",
        f"noto_{FONT_TYPE_LOWER}_{FONT_LANG_LOWER}_{font_style}",
    )

    os.makedirs(output_dir, exist_ok=True)

    r = requests.get(
        CSS_URL_PTN.format_map(
            {
                "font_type": FONT_TYPE,
                "font_lang": FONT_LANG,
                "font_weight": font_weight,
            }
        ),
        headers=REQUESTS_HEADERS,
    )

    css = r.content.decode("utf-8")
    woff2_urls = RE_URL.findall(css) or []  # type: List[str]
    woff2_save_ptn = os.path.join(output_dir, "{filename}")

    # download WOFF2 fonts
    asyncio.run(download_font_parts(woff2_urls, woff2_save_ptn))

    # save the CSS file
    with open(os.path.join(output_dir, "css.css"), "w", newline="\n") as f:
        css_local = RE_URL.sub(replace_url_to_local, css)
        f.write(css_local)
