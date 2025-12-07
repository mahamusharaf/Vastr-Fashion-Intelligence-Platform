import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  // Removed useFocusEffect from here
} from "react-native";

// --- CORRECT IMPORT FOR NAVIGATION HOOKS ---
import { useFocusEffect } from "@react-navigation/native"; 

import Ionicons from "react-native-vector-icons/Ionicons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import ProductCard from "../components/ProductCard";

const WISHLIST_KEY = "vastr_wishlist";

export default function WishlistScreen({ navigation }) {
  const [wishlist, setWishlist] = useState([]);

  // Use useFocusEffect to reload the wishlist every time the screen is focused
  useFocusEffect(
    useCallback(() => {
      loadWishlist();
    }, [])
  );

  const loadWishlist = async () => {
    try {
      const saved = await AsyncStorage.getItem(WISHLIST_KEY);
      if (saved) {
        setWishlist(JSON.parse(saved));
      }
    } catch (error) {
      console.error("Error loading wishlist:", error);
    }
  };

  const removeFromWishlist = async (productId) => {
    try {
      const updated = wishlist.filter((item) => item.product_id !== productId);
      setWishlist(updated);
      await AsyncStorage.setItem(WISHLIST_KEY, JSON.stringify(updated));
    } catch (error) {
      console.error("Error removing from wishlist:", error);
    }
  };

  if (wishlist.length === 0) {
    return (
      <View style={styles.emptyState}>
        <Ionicons name="heart-outline" size={80} color="#e8e8e8" />
        <Text style={styles.emptyTitle}>Your wishlist is empty</Text>
        <Text style={styles.emptySubtitle}>Save your favorite items here</Text>
        <TouchableOpacity
          style={styles.primaryButton}
          onPress={() => navigation.navigate("HomeTab")} // Navigate to the Tab name
        >
          <Text style={styles.primaryButtonText}>Start Shopping</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.productGrid}>
        {wishlist.map((product) => (
          <ProductCard 
            key={product.product_id} 
            product={product} 
            navigation={navigation}
            showRemove={true} // New prop to show the remove button
            onRemove={removeFromWishlist} // New handler for removal
          />
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 40,
    backgroundColor: "#fff",
  },
  emptyTitle: { fontSize: 20, fontWeight: "600", marginTop: 16, marginBottom: 8 },
  emptySubtitle: { fontSize: 14, color: "#666", marginBottom: 24 },
  primaryButton: {
    backgroundColor: "#d81b60",
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 25,
  },
  primaryButtonText: { color: "#fff", fontSize: 15, fontWeight: "600" },
  productGrid: { flexDirection: "row", flexWrap: "wrap", padding: 8 },
});