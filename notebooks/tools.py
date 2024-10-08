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

def _get_general_info(soup, recipes) -> dict:

    # link = recipes.iloc[0]['link']
    categories = ', '.join(recipes['category'].tolist())
    categories_slug = ', '.join(recipes['category_slug'].tolist())

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

    ingredients = _get_ingredients(soup)
    ingredients = ingredients if ingredients else "N/A"
    # if begins with "- " delete that
    if ingredients.startswith("- "):
        ingredients = ingredients[2:]
    # the current structure is a string -{ingrediente}\n, I need a list of ingredients separated by commas
    ingredients = ingredients.split("\n- ")

    general_info = {
        "categories": categories,
        "categories_slug": categories_slug,
        # "source": link,
        "preparation_time": tpreparacion,
        "cooking_time": tcocinar,
        "difficulty": tdificulty,
        "ingredients": ', '.join(ingredients),
    }


    # return general_info
    return '\n'.join([f'{key}: {value}' for key, value in general_info.items()])

def _get_ingredients(soup) -> list:
    ing_cnt = soup.find("div", id="ingredients-original")
    if ing_cnt is None:  # Manejo del caso donde no se encuentra el contenedor
        return None

    ingredients_labels = ing_cnt.find_all("label", class_="receta-containercheck")
    ingredients = [clean(label.get_text(strip=True)) for label in ingredients_labels]

    return "\n".join(f"- {ingredient}" for ingredient in ingredients)
    # return [clean(ingredient) for ingredient in ingredients]

def _get_preparation(soup) -> dict:
    """Extract the preparation steps from the HTML content."""
    prep_cnt = soup.find("div", class_="recipe-intro-data-pasos-normal")

    if prep_cnt is None:  # Manejo del caso donde no se encuentra el contenedor
        return None

    steps_labels = prep_cnt.find_all("label", class_="receta-containercheck")
    steps = [clean(step.get_text(strip=True)) for step in steps_labels]

    return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))
    # return [clean(step) for step in steps]

def get_presentation_and_tips(soup) -> tuple:
    """Extract the presentation and tips from the HTML content."""
    presentation_table = soup.find("table", class_="recipe-table-presentacion-tips")
    if not presentation_table:
        return None, None

    presentation, tips = None, None
    for td in presentation_table.find_all('td'):
        h2 = td.find('h2')
        if not h2:
            continue
        text = h2.get_text(strip=True)
        if text == 'Presentación':
            presentation = h2.find_next_sibling(text=True).strip()
        elif text == 'Tips':
            tips = h2.find_next_sibling(text=True).strip()

    return presentation, tips

def _get_description(soup) -> str:
    """Extract the description from the HTML content."""
    # Selector CSS para obtener todo el texto y luego procesarlo
    intro_text_full = soup.select_one('.recipe-intro-receta-normal')

    if not intro_text_full:
        return None
    # Here you could clean the text by removing the parts you are not interested in
    # Example: cutting at the first appearance of 'Revisado por'
    intro_text_clean = intro_text_full.get_text().split('Revisado por')[0].strip()

    return clean(intro_text_clean)

def make_recipe_md(soup, name, recipe_rows) -> str:
    """Create a md structure with the recipe information."""
    info = _get_general_info(soup, recipe_rows)
    ingredients = _get_ingredients(soup)
    preparation = _get_preparation(soup)
    presentation, tips = get_presentation_and_tips(soup)
    description = _get_description(soup)

    content = f"""---
{info}
---

# {name}

{description}

## Ingredients

{ingredients}

## Preparation

{preparation}

## Presentation

{presentation}

## Tips

{tips}
"""

    return content
