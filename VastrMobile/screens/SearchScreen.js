import React, { useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  FlatList,
  ActivityIndicator,
  SafeAreaView,
} from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";
// --- IMPORT CENTRALIZED COMPONENT ---
import ProductCard from "../components/ProductCard";

// Use your computer's LAN IP for real device testing
const API_BASE = "http://192.168.18.22:8000/api/v1";

export default function SearchScreen({ route, navigation }) {
  // Use the query passed from the HomeScreen search bar, or start empty
  const initialQuery = route.params?.query || ""; 
  
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  // Effect to trigger search when the screen opens with an initial query
  useEffect(() => {
    if (initialQuery) {
      handleSearch(initialQuery);
    }
  }, [initialQuery]);

  // Use useCallback to memoize the search function and prevent unnecessary re-creations
  const handleSearch = useCallback(async (query) => {
    if (query.trim().length < 2) {
      setProducts([]);
      setHasSearched(true);
      return;
    }

    setLoading(true);
    setHasSearched(true);
    
    try {
      // NOTE: Replace this with your actual search API endpoint
      const url = `${API_BASE}/products?search=${encodeURIComponent(query)}&limit=50`;
      
      const response = await fetch(url);
      const data = await response.json();

      setProducts(data.products || []);
    } catch (error) {
      console.error("Search API Error:", error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, []); // Empty dependency array means this function is created once

  const handleTextChange = (text) => {
    setSearchQuery(text);
    // Optional: Auto-search on text change (debouncing is highly recommended in production)
    // if (text.length >= 3) {
    //   handleSearch(text);
    // }
  };
  
  // Custom Header/Search Bar for the top of the screen
  const SearchHeader = () => (
    <View style={styles.header}>
      <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
        <Ionicons name="arrow-back" size={24} color="#000" />
      </TouchableOpacity>
      <View style={styles.searchInputContainer}>
        <Ionicons name="search-outline" size={20} color="#999" style={{marginLeft: 8}}/>
        <TextInput
          style={styles.searchInput}
          placeholder="Search products, brands..."
          placeholderTextColor="#999"
          value={searchQuery}
          onChangeText={handleTextChange}
          onSubmitEditing={() => handleSearch(searchQuery)}
          autoFocus={true} // Focus input when screen loads
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery("")} style={styles.clearButton}>
            <Ionicons name="close-circle" size={20} color="#999" />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  // Content to display in the list body
  const renderContent = () => {
    if (loading) {
      return (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#d81b60" />
        </View>
      );
    }

    if (hasSearched && products.length === 0) {
      return (
        <View style={styles.centered}>
          <Ionicons name="pricetag-outline" size={60} color="#e8e8e8" />
          <Text style={styles.noResultsText}>No results found for "{searchQuery}"</Text>
          <Text style={styles.noResultsSubText}>Try a different spelling or keyword.</Text>
        </View>
      );
    }
    
    // Use FlatList with numColumns=2 for the product grid
    return (
      <FlatList
        data={products}
        keyExtractor={(item) => item.product_id.toString()}
        numColumns={2}
        contentContainerStyle={styles.gridContainer}
        renderItem={({ item }) => (
          // --- RENDER CENTRALIZED PRODUCT CARD ---
          <ProductCard 
            key={item.product_id} 
            product={item} 
            navigation={navigation} 
          />
        )}
        // Ensures the whole screen view is covered
        style={{ flex: 1 }} 
      />
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <SearchHeader />
      <View style={styles.resultsContainer}>
        {renderContent()}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: "#fff" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    paddingHorizontal: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  backButton: { padding: 5 },
  searchInputContainer: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
    borderRadius: 25,
    paddingRight: 10,
    marginLeft: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 8,
    fontSize: 16,
    color: "#333",
  },
  clearButton: { padding: 5 },
  
  resultsContainer: { flex: 1, backgroundColor: "#fff" },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 40,
  },
  noResultsText: { 
    fontSize: 18, 
    fontWeight: "700", 
    marginTop: 16, 
    textAlign: 'center' 
  },
  noResultsSubText: {
    fontSize: 14,
    color: "#999",
    marginTop: 8,
    textAlign: 'center'
  },
  gridContainer: { 
    paddingHorizontal: 4, 
    minHeight: '100%' 
  }
});