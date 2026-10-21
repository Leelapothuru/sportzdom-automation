import os


def dump_state(driver, name, out_dir="inspect_output"):
    """Save page source XML and a screenshot for the current screen.

    This is what Appium Inspector shows you interactively; dumping it to
    files lets Claude read the element hierarchy and pick locators.
    """
    os.makedirs(out_dir, exist_ok=True)
    xml_path = os.path.join(out_dir, f"{name}.xml")
    png_path = os.path.join(out_dir, f"{name}.png")

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    driver.save_screenshot(png_path)

    print(f"Dumped: {xml_path}, {png_path}")
    return xml_path, png_path
