class Listing:
    def __init__(self, image_src, title, price, post_url, location):
        self.image_src = image_src
        self.title = title
        self.price = price
        self.post_url = post_url
        self.location = location

    def __repr__(self):
        return f"Listing(title={self.title}, price={self.price}, location={self.location}, url={self.post_url})"
