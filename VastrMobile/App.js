// App.js
import React from "react";
import { StatusBar } from "react-native";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import Ionicons from "react-native-vector-icons/Ionicons";

import HomeScreen, { AllProductsScreen } from "./screens/HomeScreen";
import ProductScreen from "./screens/ProductScreen";
import SearchScreen from "./screens/SearchScreen";
import WishlistScreen from "./screens/WishlistScreen";
import ProfileScreen from "./screens/ProfileScreen";
// --- NEW IMPORTS for Placeholder Screens ---
import SettingsScreen from "./screens/SettingsScreen";
import SupportScreen from "./screens/SupportScreen"; 


const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// --- 1. Home Stack Navigator ---
function HomeStack() {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="HomeFeed" component={HomeScreen} />
      <Stack.Screen name="AllProducts" component={AllProductsScreen} />
    </Stack.Navigator>
  );
}

// --- 2. Bottom Tabs Navigator ---
function Tabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: "#d81b60",
        tabBarInactiveTintColor: "#999",
        tabBarStyle: { borderTopWidth: 1, borderTopColor: "#e8e8e8", height: 60, paddingBottom: 5 },
        tabBarLabelStyle: { fontSize: 12 },
        tabBarIcon: ({ color }) => {
          let iconName;
          if (route.name === "HomeTab") iconName = "home";
          else if (route.name === "Wishlist") iconName = "heart";
          else if (route.name === "Profile") iconName = "person";
          return <Ionicons name={iconName + "-outline"} size={24} color={color} />;
        },
      })}
    >
      <Tab.Screen
        name="HomeTab"
        component={HomeStack}
        options={{ title: "Home" }}
      />
      <Tab.Screen name="Wishlist" component={WishlistScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

// --- 3. Main Stack Navigator ---
export default function App() {
  return (
    <NavigationContainer>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {/* Main Tabs entry point */}
        <Stack.Screen name="MainTabs" component={Tabs} />

        {/* Full-screen pages (hiding tabs) */}
        <Stack.Screen name="Product" component={ProductScreen} />
        <Stack.Screen name="Search" component={SearchScreen} />
        
        {/* --- NEW PROFILE-RELATED SCREENS --- */}
        <Stack.Screen 
            name="Settings" 
            component={SettingsScreen} 
            options={{ headerShown: true, headerTitle: "Account Settings" }}
        />
        <Stack.Screen 
            name="Support" 
            component={SupportScreen} 
            options={{ headerShown: true, headerTitle: "Help & Support" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}