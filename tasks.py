from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.PDF import PDF
from RPA.Tables import Tables
from RPA.Archive import Archive
from time import sleep

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(
        slowmo=100,
    )
    open_robot_order_website()
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
    archive_receipts()

def open_robot_order_website():
    """Navigates to the given URL"""
    browser.goto("https://robotsparebinindustries.com/#/robot-order")

def get_orders():
    """Gets order"""
    http = HTTP()
    http.download(url="https://robotsparebinindustries.com/orders.csv", overwrite=True)
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders

def close_annoying_modal():
    """Closes modal that appear when opening the website"""
    page = browser.page()
    page.click("text=OK")

def fill_the_form(order):
    """Fills the form using the data from each CSV row"""
    page = browser.page()
    while True:
        page.select_option("#head", order["Head"])
        page.click(f"#id-body-{order['Body']}")
        page.fill("input[placeholder='Enter the part number for the legs']", order["Legs"])
        page.fill("#address", order["Address"])
        page.click("button:text('Order')")
        sleep(1)
        if page.locator('.alert-danger').is_visible():
            print("Repeating...")
            continue
        break
    store_receipt_as_pdf(order['Order number'])
    page.wait_for_selector("button:text('Order another robot')", timeout=10000)
    page.click("button:text('Order another robot')")

def store_receipt_as_pdf(order_number):
    """Export the receipt to a PDF file"""
    pdf_path = f"output/receipts/{order_number}.pdf"
    page = browser.page()

    receipt_html = page.locator("#receipt").inner_html()
    screenshot_path = screenshot_robot(order_number)
    full_html = embed_screenshot_to_receipt(screenshot_path, receipt_html)

    pdf = PDF()
    pdf.html_to_pdf(full_html, pdf_path)

def screenshot_robot(order_number):
    """Take a screenshot of the robot image"""
    image_path = f"output/receipts/{order_number}.png"
    page = browser.page()
    page.locator("#robot-preview-image").screenshot(path=image_path)
    return image_path

def embed_screenshot_to_receipt(screenshot_path, receipt_html):
    """Embed the screenshot into the HTML content of the receipt"""
    full_html = f"""
    <html>
        <body>
            {receipt_html}
            <div><img src="{screenshot_path}" style="max-width:100%; margin-top:20px;"/></div>
        </body>
    </html>
    """
    return full_html

def archive_receipts():
    archive = Archive()
    archive.archive_folder_with_zip(
        folder="output/receipts",
        archive_name="output/receipts.zip",
        include="*.pdf"
    )
