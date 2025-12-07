import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  Image,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  FlatList,
  Linking, // --- NEW IMPORT ---
} from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";
import AsyncStorage from "@react-native-async-storage/async-storage"; // --- NEW IMPORT ---
import ProductCard from "../components/ProductCard"; // --- NEW IMPORT for list view ---

// Use your computer's LAN IP for real device testing
const API_BASE = "http://192.168.18.22:8000/api/v1";
const WISHLIST_KEY = "vastr_wishlist"; // Define constant for AsyncStorage

export default function ProductScreen({ route, navigation }) {
  const product = route.params?.product; // single product if passed
  const brandFilter = route.params?.brand; // optional brand filter for "View All"

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  // --- NEW STATE for Wishlist ---
  const [isWishlisted, setIsWishlisted] = useState(false); 

  useEffect(() => {
    if (product) {
      checkWishlistStatus(product.product_id);
    } else {
      fetchAllProducts();
    }
  }, [product]);

  // --- NEW: Wishlist Functions ---
  const checkWishlistStatus = async (productId) => {
    try {
      const saved = await AsyncStorage.getItem(WISHLIST_KEY);
      const list = saved ? JSON.parse(saved) : [];
      setIsWishlisted(list.some(item => item.product_id === productId));
    } catch (error) {
      console.error("Error checking wishlist status:", error);
      setIsWishlisted(false);
    }
  };

  const toggleWishlist = async () => {
    if (!product) return;
    try {
      const saved = await AsyncStorage.getItem(WISHLIST_KEY);
      let list = saved ? JSON.parse(saved) : [];
      
      if (isWishlisted) {
        // Remove from wishlist
        list = list.filter(item => item.product_id !== product.product_id);
        Alert.alert("Removed", `${product.title} removed from wishlist.`);
      } else {
        // Add to wishlist
        list.push(product);
        Alert.alert("Added", `${product.title} added to wishlist!`);
      }
      
      await AsyncStorage.setItem(WISHLIST_KEY, JSON.stringify(list));
      setIsWishlisted(!isWishlisted);
    } catch (error) {
      console.error("Error toggling wishlist:", error);
      Alert.alert("Error", "Could not update wishlist.");
    }
  };

  // ... (fetchAllProducts function remains the same) ...
  const fetchAllProducts = async () => {
    setLoading(true);
    try {
      let url = `${API_BASE}/products?limit=100`;
      if (brandFilter) url += `&brand=${encodeURIComponent(brandFilter)}`;

      const res = await fetch(url);
      const text = await res.text();
      let data = {};
      try {
        data = JSON.parse(text);
      } catch (err) {
        console.warn("Failed to parse JSON:", text);
      }

      setProducts(data.products || []);
    } catch (err) {
      console.error("Error fetching products:", err);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };


  // Single Product View
  if (product) {
    const imageUrl =
      product.images?.[0]?.src || product.images?.[0] || "https://via.placeholder.com/600";
    const proxyUrl = `https://images.weserv.nl/?url=${encodeURIComponent(
      imageUrl
    )}&w=800&h=1000&fit=cover&output=webp&q=85`;

    const handleBuy = () => {
      if (product.product_url) {
        // Using Linking as required
        Linking.openURL(product.product_url).catch(() => { 
          Alert.alert("Error", "Cannot open this link");
        });
      } else {
        Alert.alert("Link not available", "This product doesn't have a link yet.");
      }
    };

    return (
      <ScrollView style={styles.container}>
        {/* Back Button */}
        <TouchableOpacity
          style={styles.backBtn}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={28} color="#000" />
        </TouchableOpacity>
        
        {/* --- NEW: Wishlist Button --- */}
        <TouchableOpacity style={styles.wishlistBtn} onPress={toggleWishlist}>
          <Ionicons 
            name={isWishlisted ? "heart" : "heart-outline"} 
            size={28} 
            color={isWishlisted ? "#d81b60" : "#000"} 
          />
        </TouchableOpacity>


        {/* Main Image */}
        <Image source={{ uri: proxyUrl }} style={styles.image} resizeMode="cover" />

        <View style={styles.content}>
          <Text style={styles.brand}>{product.brand_name}</Text>
          <Text style={styles.title}>{product.title}</Text>

          <View style={styles.priceContainer}>
            <Text style={styles.price}>
              PKR {product.price_min?.toLocaleString() || "N/A"}
            </Text>
            {product.original_price && product.original_price > product.price_min && (
              <Text style={styles.originalPrice}>
                PKR {product.original_price.toLocaleString()}
              </Text>
            )}
            {product.is_sale && <Text style={styles.saleTag}>SALE</Text>}
          </View>

          {product.in_stock === false && (
            <Text style={styles.outOfStock}>Out of Stock</Text>
          )}

          <TouchableOpacity
            style={[
              styles.buyButton,
              (!product.product_url || product.in_stock === false) &&
                styles.buyButtonDisabled,
            ]}
            onPress={handleBuy}
            disabled={!product.product_url || product.in_stock === false}
          >
            <Text style={styles.buyButtonText}>
              {product.in_stock === false
                ? "Out of Stock"
                : "Buy from " + product.brand_name}
            </Text>
          </TouchableOpacity>

          <View style={styles.infoRow}>
            <Ionicons name="open-outline" size={16} color="#666" />
            <Text style={styles.infoText}>
              Opens in {product.brand_name}'s official website
            </Text>
          </View>
        </View>
      </ScrollView>
    );
  }

  // All Products View (List when no single product is passed)
  return (
    <View style={{ flex: 1, backgroundColor: "#fff" }}>
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#d81b60" />
        </View>
      ) : (
        <FlatList
          data={products}
          keyExtractor={(item) => item.product_id.toString()}
          numColumns={2}
          contentContainerStyle={{ padding: 8 }}
          renderItem={({ item }) => (
            // --- USE CENTRALIZED PRODUCT CARD ---
            <ProductCard 
                key={item.product_id} 
                product={item} 
                navigation={navigation} 
            />
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  backBtn: {
    position: "absolute",
    top: 50,
    left: 16,
    zIndex: 10,
    backgroundColor: "rgba(255,255,255,0.9)",
    padding: 8,
    borderRadius: 20,
  },
  // --- NEW: Wishlist button style ---
  wishlistBtn: {
    position: "absolute",
    top: 50,
    right: 16,
    zIndex: 10,
    backgroundColor: "rgba(255,255,255,0.9)",
    padding: 8,
    borderRadius: 20,
  },
  image: { width: "100%", height: 520 },
  content: { padding: 20 },
  brand: { fontSize: 15, fontWeight: "700", color: "#d81b60", marginBottom: 4 },
  title: { fontSize: 20, fontWeight: "700", lineHeight: 28, marginBottom: 12 },
  priceContainer: { flexDirection: "row", alignItems: "center", marginBottom: 16 },
  price: { fontSize: 26, fontWeight: "800", color: "#000" },
  originalPrice: {
    fontSize: 18,
    color: "#999",
    textDecorationLine: "line-through",
    marginLeft: 12,
  },
  saleTag: {
    backgroundColor: "#d81b60",
    color: "#fff",
    fontSize: 12,
    fontWeight: "700",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
    marginLeft: 12,
  },
  outOfStock: {
    color: "#d81b60",
    fontWeight: "700",
    fontSize: 16,
    textAlign: "center",
    marginVertical: 16,
  },
  buyButton: {
    backgroundColor: "#d81b60",
    padding: 18,
    borderRadius: 12,
    alignItems: "center",
    marginVertical: 20,
  },
  buyButtonDisabled: { backgroundColor: "#ccc" },
  buyButtonText: { color: "#fff", fontSize: 18, fontWeight: "700" },
  infoRow: { flexDirection: "row", alignItems: "center" },
  infoText: { marginLeft: 8, color: "#666", fontSize: 14 },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  // ProductCard styles removed as they are now in ProductCard.js
});