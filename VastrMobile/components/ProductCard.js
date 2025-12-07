import React from "react";
import { View, Text, Image, TouchableOpacity, StyleSheet } from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";

// Use a centralized ProductCard component for consistency across Home, Search, and Wishlist
export default function ProductCard({ product, navigation, showRemove = false, onRemove }) {
  // --- Image Handling ---
  const imageUrl = product.images?.[0]?.src || product.images?.[0] || "https://via.placeholder.com/300x400";
  // Image proxy for better performance (as seen in your original code)
  const proxyUrl = imageUrl.includes("placeholder")
    ? imageUrl
    : `https://images.weserv.nl/?url=${encodeURIComponent(imageUrl)}&w=400&h=600&fit=cover&output=webp&q=85`;

  // --- Discount Calculation (New Enhancement) ---
  let discount = null;
  const priceMin = product.price_min || 0;
  const originalPrice = product.original_price || 0;

  if (originalPrice > priceMin && priceMin > 0) {
    discount = Math.round(((originalPrice - priceMin) / originalPrice) * 100);
  }

  return (
    <TouchableOpacity
      style={styles.productCard}
      onPress={() => navigation.navigate("Product", { product })}
    >
      {/* Remove Button for Wishlist Screen */}
      {showRemove && onRemove && (
        <TouchableOpacity style={styles.removeBtn} onPress={() => onRemove(product.product_id)}>
          <Ionicons name="close" size={16} color="#000" />
        </TouchableOpacity>
      )}

      <Image source={{ uri: proxyUrl }} style={styles.productImage} />
      
      {/* Discount Badge */}
      {discount && (
        <View style={styles.discountBadge}>
          <Text style={styles.discountText}>-{discount}%</Text>
        </View>
      )}

      <View style={styles.productInfo}>
        <Text style={styles.brandName}>{product.brand_name || "Unknown Brand"}</Text>
        <Text style={styles.productName} numberOfLines={2}>
          {product.title}
        </Text>
        <Text style={styles.price}>
          PKR {priceMin.toLocaleString() || "N/A"}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  productCard: { width: "50%", padding: 8, position: "relative" },
  productImage: { 
    width: "100%", 
    aspectRatio: 0.7, 
    borderRadius: 8, 
    backgroundColor: "#f5f5f5" 
  },
  productInfo: { marginTop: 8 },
  brandName: { fontSize: 12, fontWeight: "700", color: "#d81b60", marginBottom: 4 },
  productName: { fontSize: 13, color: "#333", lineHeight: 18, marginBottom: 6 },
  price: { fontSize: 15, fontWeight: "800", color: "#000" },
  
  // New Styles for enhancements
  discountBadge: {
    position: "absolute",
    top: 16,
    left: 16,
    backgroundColor: "#d81b60", // Sale color
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    zIndex: 5,
  },
  discountText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
  },
  removeBtn: {
    position: "absolute",
    top: 16,
    right: 16,
    backgroundColor: "rgba(255, 255, 255, 0.9)", // slightly transparent white
    borderRadius: 16,
    width: 32,
    height: 32,
    justifyContent: "center",
    alignItems: "center",
    zIndex: 10,
    borderWidth: 1,
    borderColor: "#e8e8e8",
  },
});