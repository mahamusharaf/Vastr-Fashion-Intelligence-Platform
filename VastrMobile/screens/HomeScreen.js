import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
} from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";
// --- IMPORT CENTRALIZED COMPONENT ---
import ProductCard from "../components/ProductCard"; 

// Use your computer's LAN IP for real device testing
const API_BASE = "http://192.168.18.22:8000/api/v1";

export default function HomeScreen({ navigation }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  useEffect(() => {
    fetchData();
  }, []);
// ... (fetchData and onRefresh functions remain the same) ...
  const fetchData = async () => {
    setLoading(true);
    try {
      const [productsRes, categoriesRes, brandsRes] = await Promise.all([
        fetch(`${API_BASE}/products?limit=24`),
        fetch(`${API_BASE}/categories`),
        fetch(`${API_BASE}/brands`),
      ]);

      const parseJSON = async (res) => {
        const text = await res.text();
        try {
          return JSON.parse(text);
        } catch {
          return {};
        }
      };

      const productsData = await parseJSON(productsRes);
      const categoriesData = await parseJSON(categoriesRes);
      const brandsData = await parseJSON(brandsRes);

      setProducts(productsData.products || []);
      setCategories([
        "All",
        ...(categoriesData.categories?.slice(0, 5).map((c) => c.category_name) || []),
      ]);
      setBrands(brandsData.brands?.slice(0, 6) || []);
    } catch (error) {
      console.error("Error fetching data:", error);
      setProducts([]);
      setCategories(["All", "Women", "Brands", "Sale"]);
      setBrands([]);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      // Navigate to the Search Stack Screen
      navigation.navigate("Search", { query: searchQuery }); 
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#d81b60" />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search-outline" size={20} color="#999" />
        <TextInput
          style={styles.searchInput}
          placeholder="Search products, brands..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          onSubmitEditing={handleSearch}
          placeholderTextColor="#999"
        />
      </View>
      
      {/* Categories Bar (NEW: Horizontal Scroll) */}
      <View style={styles.categoryBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {categories.map((category) => (
            <TouchableOpacity 
              key={category} 
              style={[
                styles.categoryChip, 
                selectedCategory === category && styles.categoryChipActive
              ]}
              onPress={() => setSelectedCategory(category)}
            >
              <Text style={[
                styles.categoryText,
                selectedCategory === category && styles.categoryTextActive
              ]}>
                {category}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Products Preview */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Latest Arrivals</Text>
          <TouchableOpacity
            // Using the HomeStack navigation defined in App.js
            onPress={() => navigation.navigate("AllProducts", { products })} 
          >
            <Text style={styles.viewAll}>View All</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.productGrid}>
          {products.slice(0, 6).map((product) => (
            // --- USE CENTRALIZED PRODUCT CARD ---
            <ProductCard 
                key={product.product_id} 
                product={product} 
                navigation={navigation} 
            />
          ))}
        </View>
      </View>
    </ScrollView>
  );
}

// All Products Screen (Keep here, but update to use ProductCard)
export function AllProductsScreen({ route, navigation }) {
  const { products } = route.params;

  return (
    <ScrollView style={{ flex: 1, backgroundColor: "#fff" }}>
      <Text style={{ fontSize: 22, fontWeight: "700", margin: 16 }}>All Products</Text>
      <View style={{ flexDirection: "row", flexWrap: "wrap" }}>
        {products.map((product) => (
          // --- USE CENTRALIZED PRODUCT CARD ---
          <ProductCard 
            key={product.product_id} 
            product={product} 
            navigation={navigation} 
          />
        ))}
      </View>
    </ScrollView>
  );
}

// --- REMOVE ProductCard COMPONENT FROM HERE ---

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  searchContainer: {
    flexDirection: "row",
    alignItems: "center",
    margin: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#f5f5f5",
    borderRadius: 25,
  },
  searchInput: { flex: 1, marginLeft: 8, fontSize: 16, color: "#333" },
  
  // New Styles for Category Bar
  categoryBar: {
    marginBottom: 24,
    paddingHorizontal: 16,
  },
  categoryChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#f0f0f0",
    marginRight: 8,
  },
  categoryChipActive: {
    backgroundColor: "#d81b60",
  },
  categoryText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  categoryTextActive: {
    color: "#fff",
  },
  
  // Existing Styles
  section: { paddingHorizontal: 16, marginBottom: 24 },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 16 },
  sectionTitle: { fontSize: 18, fontWeight: "700" },
  viewAll: { fontSize: 14, color: "#d81b60", textDecorationLine: "underline" },
  productGrid: { flexDirection: "row", flexWrap: "wrap" },
  // productCard styles removed as they are in ProductCard.js
});