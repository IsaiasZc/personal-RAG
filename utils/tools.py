import re

from typing import Any, cast
from playwright.async_api import async_playwright
from bs4 import Tag

async def fetch_content_with_playwright(url, filepath):
    """ Fetch content of a webpage using Playwright and save it to a file."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        content = await page.content()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        await browser.close()

def clean(text: Any) -> str:
    """Convert text to a string and clean it."""
    if text is None:
        return ""
    if isinstance(text, Tag):
        text = text.get_text()
    if not isinstance(text, str):
        text = str(text)
    # Replace non-breaking space with normal space and remove surrounding whitespace.
    text = text.replace(" ", " ").replace("\u200b", "").replace("\u200a", " ")
    text = re.sub(r"(\n\s*)+\n", "\n\n", text)
    text = re.sub(r" +\n", "\n", text)
    return cast(str, text.strip())

# * The next functions are used to extract the recipe information from the HTML content

def _get_general_info(soup, link) -> dict:
    e_preparacion = soup.select_one(
        "div.recipe-info-tiempos-nivel .icon-k7-receta-tpreparacion span"
    )
    tpreparacion = clean(e_preparacion.get_text()) if e_preparacion else "N/A"
    e_tcocinar = soup.select_one(
        "div.recipe-info-tiempos-nivel .icon-k7-receta-tcocinar span"
    )
    tcocinar = clean(e_tcocinar.get_text()) if e_tcocinar else "N/A"
    e_tdificulty = soup.select_one(
        "div.recipe-info-tiempos-nivel .icon-k7-receta-tdificultad span"
    )
    tdificulty = clean(e_tdificulty.get_text()) if e_tdificulty else "N/A"

    general_info = {
        "source": link,
        "prep_time": tpreparacion,
        "cook_time": tcocinar,
        "difficulty": tdificulty,
    }

    return general_info

def _get_ingredients(soup) -> list:
    ing_cnt = soup.find("div", id="ingredients-original")
    if ing_cnt is None:  # Manejo del caso donde no se encuentra el contenedor
        return None

    ingredients_labels = ing_cnt.find_all("label", class_="receta-containercheck")
    ingredients = [clean(label.get_text(strip=True)) for label in ingredients_labels]

    return "\n".join(ingredients)
    # return [clean(ingredient) for ingredient in ingredients]

def _get_preparation(soup) -> dict:
    """Extract the preparation steps from the HTML content."""
    prep_cnt = soup.find("div", class_="recipe-intro-data-pasos-normal")

    if prep_cnt is None:  # Manejo del caso donde no se encuentra el contenedor
        return None

    steps_labels = prep_cnt.find_all("label", class_="receta-containercheck")
    steps = [clean(step.get_text(strip=True)) for step in steps_labels]

    return "\n".join(steps)
    # return [clean(step) for step in steps]

def make_recipe_md(soup, name, link) -> str:
    """Create a md structure with the recipe information."""
    info = _get_general_info(soup, link)
    ingredients = _get_ingredients(soup)
    preparation = _get_preparation(soup)

    content = f"""
---
{info}
---
# {name}

## Ingredients
{ingredients}

## Preparation
{preparation}
"""

    return content
