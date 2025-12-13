import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Dimensions
} from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";
import { SafeAreaView } from 'react-native-safe-area-context';
import ProductCard from "../components/ProductCard";

const API_BASE = "http://192.168.18.22:8000/api/v1";

export default function HomeScreen({ navigation }) {
  const [latestProducts, setLatestProducts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes, brandsRes, categoriesRes] = await Promise.all([
          fetch(`${API_BASE}/products?limit=6`),
          fetch(`${API_BASE}/brands`),
          fetch(`${API_BASE}/categories`),
        ]);

        const productsData = await productsRes.json();
        const brandsData = await brandsRes.json();
        const categoriesData = await categoriesRes.json();

        setLatestProducts(productsData.products || []);
        setBrands(brandsData.brands || []);
        setCategories(categoriesData.categories || []);

        console.log('✅ Categories loaded:', categoriesData.categories?.length);

      } catch (error) {
        console.error("Home screen fetch error:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const renderCategory = ({ item }) => (
    <TouchableOpacity
        style={styles.categoryCard}
        onPress={() => {
            console.log('Category clicked:', item.category_name);
            navigation.navigate("AllProducts", {
                title: item.category_name,
                filter: { category: item.category_name }
            });
        }}
    >
        <Text style={styles.categoryName} numberOfLines={1}>
            {item.category_name || 'Category N/A'}
        </Text>
        <Text style={styles.categoryItems}>
            <Text>{(item.product_count?.toLocaleString() || '0')}</Text>
            <Text> items</Text>
        </Text>
    </TouchableOpacity>
  );

  const renderBrand = ({ item }) => (
    <TouchableOpacity
        style={styles.brandCard}
        onPress={() => {
            console.log('Brand clicked:', item.brand_name);
            navigation.navigate("AllProducts", {
                title: item.brand_name,
                filter: { brand: item.brand_name }
            });
        }}
    >
        <Text style={styles.brandName} numberOfLines={1}>
            {item.brand_name || 'Brand N/A'}
        </Text>
        <Text style={styles.brandItems}>
            <Text>{(item.product_count?.toLocaleString() || '0')}</Text>
            <Text> items</Text>
        </Text>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#d81b60" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView style={styles.container}>
        {/* ✅ UPDATED HEADER - Logo as Text (Like Web) */}
        <View style={styles.header}>
            <Text style={styles.logo}>VASTR</Text>
            <TouchableOpacity
                style={styles.searchBar}
                onPress={() => navigation.navigate("Search")}
            >
                <Ionicons name="search-outline" size={18} color="#999" />
                <Text style={styles.searchText}>Search products, brands...</Text>
            </TouchableOpacity>
        </View>

        {/* Shop by Category */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { paddingHorizontal: 15, marginBottom: 10 }]}>
            <Text>Shop fashion from </Text>
            <Text style={{fontWeight: '900'}}>{categories.length}+</Text>
            <Text> categories</Text>
          </Text>
          <FlatList
            data={categories}
            renderItem={renderCategory}
            keyExtractor={(item, index) => item.category_name || `category-${index}`}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.flatListContainer}
          />
        </View>

        {/* Shop by Brand */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Shop by Brand</Text>
            <TouchableOpacity
                onPress={() => navigation.navigate("AllProducts", { title: "All Brands" })}
            >
              <Text style={styles.viewAll}>View All Brands</Text>
            </TouchableOpacity>
          </View>
          <FlatList
            data={brands}
            renderItem={renderBrand}
            keyExtractor={(item, index) => item.brand_id || `brand-${index}`}
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.flatListContainer}
          />
        </View>

        {/* Latest Arrivals */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Latest Arrivals</Text>
            <TouchableOpacity
                onPress={() => navigation.navigate("AllProducts", { title: "Latest Arrivals" })}
            >
              <Text style={styles.viewAll}>View All</Text>
            </TouchableOpacity>
          </View>
          <FlatList
            data={latestProducts}
            renderItem={({ item }) => (
                <ProductCard product={item} navigation={navigation} />
            )}
            keyExtractor={(item, index) => item.product_id?.toString() || `latest-product-${index}`}
            numColumns={2}
            scrollEnabled={false}
            contentContainerStyle={styles.gridContainer}
          />
        </View>

        <View style={{ height: 50 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
    safeArea: { flex: 1, backgroundColor: '#fff' },
    container: { flex: 1, backgroundColor: "#fff" },
    centered: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#fff" },

    // ✅ UPDATED HEADER STYLES - Matches Web
    header: {
        padding: 15,
        paddingBottom: 10,
        flexDirection: 'row',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#e8e8e8'
    },
    logo: {
        fontSize: 24,           // Matches web: 1.8rem
        fontWeight: '900',      // Matches web: 700 (but 900 is bolder, better for mobile)
        color: '#000',          // Matches web
        letterSpacing: -1,      // Matches web: -1px
        marginRight: 15
    },
    searchBar: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',  // Matches web: #f8f8f8
        borderRadius: 20,
        paddingHorizontal: 10,
        paddingVertical: 8,
        borderWidth: 1,
        borderColor: '#e8e8e8'       // Added border like web
    },
    searchText: {
        marginLeft: 8,
        color: '#999',
        fontSize: 14
    },

    // Sections
    section: { paddingVertical: 15 },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingHorizontal: 15,
        marginBottom: 10
    },
    sectionTitle: { fontSize: 18, fontWeight: "700" },
    viewAll: { fontSize: 14, color: '#d81b60', fontWeight: '600' },

    // Category Cards
    flatListContainer: { paddingHorizontal: 10 },
    categoryCard: {
        width: 130,
        height: 100,
        backgroundColor: '#f8f8f8',
        borderRadius: 10,
        marginHorizontal: 5,
        justifyContent: 'flex-end',
        padding: 10,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 1,
    },
    categoryName: { fontSize: 14, fontWeight: '700', color: '#333' },
    categoryItems: { fontSize: 12, color: '#777' },

    // Brand Cards
    brandCard: {
        width: 150,
        height: 100,
        backgroundColor: '#fff',
        borderRadius: 10,
        marginHorizontal: 5,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 10,
        borderWidth: 1,
        borderColor: '#eee',
    },
    brandName: { fontSize: 16, fontWeight: '700', color: '#d81b60', textAlign: 'center' },
    brandItems: { fontSize: 12, color: '#999', marginTop: 4 },

    // Product Grid
    gridContainer: { paddingHorizontal: 4 },
    noResultsText: { fontSize: 16, color: '#666' }
});