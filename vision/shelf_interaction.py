# vision/interaction/shelf_interaction.py

import math


class ShelfInteractionDetector:
    def __init__(self, distance_threshold=50):
        """
        Detect interactions between customer and product/shelf
        """
        self.distance_threshold = distance_threshold

    def _calculate_center(self, bbox):
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def detect_interactions(self, customers, products):
        """
        Detect interactions between customers and products

        Args:
            customers: list of tracked customers
                [
                    {"id": 1, "bbox": [...]}
                ]

            products: list of product detections
                [
                    {"bbox": [...]}
                ]

        Returns:
            interactions:
                [
                    {
                        "customer_id": 1,
                        "product_bbox": [...],
                        "interaction": "near_product"
                    }
                ]
        """

        interactions = []

        for customer in customers:
            c_center = self._calculate_center(customer["bbox"])

            for product in products:
                p_center = self._calculate_center(product["bbox"])

                dist = self._distance(c_center, p_center)

                if dist < self.distance_threshold:
                    interactions.append({
                        "customer_id": customer["id"],
                        "product_bbox": product["bbox"],
                        "interaction": "near_product"
                    })

        return interactions

    def classify_interaction(self, interaction_history):
        """
        Classify behavior based on interaction patterns

        Example:
        - short interaction → browsing
        - long interaction → picking product
        """

        duration = interaction_history.get("duration", 0)

        if duration < 2:
            return "browsing"
        elif duration < 5:
            return "considering"
        else:
            return "picked_product"