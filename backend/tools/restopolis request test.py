import requests

url = "https://ssl.education.lu/eRestauration/CustomerServices/Menu/BtnChangeRestaurant?pRestaurantSelection=150"
cookies = {
    # 'CustomerServices.Restopolis.SelectedRestaurant': '150',
}

try:
    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        # Save the HTML content to a file named 'menu.html'
        with open("restopolis_menu.html", "w", encoding="utf-8") as file:
            file.write(response.text)
        print("Success! Response saved to 'restopolis_menu.html'.")
    else:
        print(f"Error: {response.status_code}")

except Exception as e:
    print(f"Error saving file: {e}")

