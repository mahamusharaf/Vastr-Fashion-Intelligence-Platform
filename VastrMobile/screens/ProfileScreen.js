import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";
import AsyncStorage from "@react-native-async-storage/async-storage";

// Use your computer's LAN IP for real device testing
const API_BASE = "http://192.168.18.22:8000/api/v1"; // Assuming auth endpoints are here

const AUTH_TOKEN_KEY = "vastr_auth_token";
const USER_DATA_KEY = "vastr_user";

export default function ProfileScreen({ navigation }) {
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState(""); // NEW: For actual login
  const [isNewUser, setIsNewUser] = useState(false); // Toggle Sign In / Sign Up
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadUser();
  }, []);

  // --- Core Utility Functions ---

  const loadUser = async () => {
    try {
      const savedUser = await AsyncStorage.getItem(USER_DATA_KEY);
      const savedToken = await AsyncStorage.getItem(AUTH_TOKEN_KEY);
      
      if (savedUser && savedToken) {
        setUser(JSON.parse(savedUser));
      }
    } catch (error) {
      console.error("Error loading user:", error);
    }
  };

  const handleAuth = async () => {
    setError(null);
    setLoading(true);
    
    // Determine the action (Login or Register) and the corresponding endpoint
    const endpoint = isNewUser ? "/auth/register" : "/auth/login";
    const actionText = isNewUser ? "Registration" : "Login";

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        if (isNewUser) {
          // --- SIMULATED EMAIL CONFIRMATION LOGIC ---
          Alert.alert(
            "Account Created!",
            "Please check your email to verify your account before logging in."
          );
          setIsNewUser(false); // Switch to login view after successful registration
        } else {
          // Successful Login
          const { token, user_data } = data; 
          
          await AsyncStorage.setItem(AUTH_TOKEN_KEY, token);
          await AsyncStorage.setItem(USER_DATA_KEY, JSON.stringify(user_data));
          
          setUser(user_data);
          Alert.alert("Success", `Welcome back, ${user_data.name || user_data.email}!`);
        }
      } else {
        // API returned an error (e.g., 401 Unauthorized, 400 Bad Request)
        setError(data.message || `An error occurred during ${actionText}.`);
      }
    } catch (err) {
      console.error(`${actionText} error:`, err);
      setError("Network or server error. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
      await AsyncStorage.removeItem(USER_DATA_KEY);
      setUser(null);
      setEmail("");
      setPassword("");
      Alert.alert("Logged Out", "You have been successfully logged out.");
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  // --- Auth View ---
  if (!user) {
    return (
      <ScrollView contentContainerStyle={styles.authContainer}>
        <Text style={styles.authTitle}>{isNewUser ? "Create Account" : "Welcome Back"}</Text>
        <Text style={styles.authSubtitle}>
          {isNewUser ? "Sign up to start saving your favorites." : "Sign in to manage your profile."}
        </Text>

        <TextInput
          style={styles.authInput}
          placeholder="Email address"
          placeholderTextColor="#999"
          keyboardType="email-address"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          textContentType="emailAddress"
        />

        <TextInput
          style={styles.authInput}
          placeholder="Password"
          placeholderTextColor="#999"
          secureTextEntry
          value={password}
          onChangeText={setPassword}
          textContentType="password"
        />

        {error && <Text style={styles.errorText}>⚠️ {error}</Text>}

        <TouchableOpacity 
          style={styles.primaryButton} 
          onPress={handleAuth}
          disabled={loading || !email || !password}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.primaryButtonText}>
              {isNewUser ? "Create Account" : "Sign In"}
            </Text>
          )}
        </TouchableOpacity>

        <TouchableOpacity onPress={() => setIsNewUser(!isNewUser)} style={{ marginTop: 20 }}>
          <Text style={styles.toggleAuthText}>
            {isNewUser
              ? "Already have an account? Sign In"
              : "Don't have an account? Create One"}
          </Text>
        </TouchableOpacity>
        
        <View style={styles.dividerContainer}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>OR</Text>
            <View style={styles.dividerLine} />
        </View>


        <TouchableOpacity style={styles.socialButton} disabled={loading}>
          <Ionicons name="logo-google" size={20} color="#4285F4" />
          <Text style={styles.socialButtonText}>Continue with Google</Text>
        </TouchableOpacity>
      </ScrollView>
    );
  }

  // --- Profile View ---
  return (
    <ScrollView style={styles.container}>
      <View style={styles.profileHeader}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>{user.name ? user.name[0].toUpperCase() : user.email[0].toUpperCase()}</Text>
        </View>
        <Text style={styles.userName}>{user.name || "User"}</Text>
        <Text style={styles.userEmail}>{user.email}</Text>
      </View>

      {menuItems.map((item, index) => (
        <TouchableOpacity
          key={index}
          style={styles.menuItem}
          onPress={() => navigation.navigate(item.screen)}
        >
          <Ionicons name={item.icon} size={20} color="#000" />
          <Text style={styles.menuTitle}>{item.title}</Text>
          <Ionicons name="chevron-forward" size={20} color="#999" />
        </TouchableOpacity>
      ))}

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout} disabled={loading}>
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

// Menu Items for the logged-in view
const menuItems = [
  { icon: "settings-outline", title: "Account Settings", screen: "Settings" },
  { icon: "heart-outline", title: "Wishlist", screen: "Wishlist" },
  { icon: "file-tray-full-outline", title: "Order History", screen: "Orders" },
  { icon: "help-circle-outline", title: "Help & Support", screen: "Support" },
];


const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  authContainer: {
    flexGrow: 1,
    padding: 24,
    justifyContent: "center",
    backgroundColor: "#fff",
  },
  authTitle: { fontSize: 24, fontWeight: "700", marginBottom: 8, textAlign: 'center' },
  authSubtitle: { fontSize: 14, color: "#666", marginBottom: 32, textAlign: 'center' },
  authInput: {
    borderWidth: 1,
    borderColor: "#e8e8e8",
    padding: 14,
    borderRadius: 8,
    fontSize: 15,
    marginBottom: 12,
  },
  primaryButton: {
    backgroundColor: "#d81b60",
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 25,
    marginTop: 16,
    alignItems: "center",
  },
  primaryButtonText: { color: "#fff", fontSize: 15, fontWeight: "600" },
  
  // Divider Styles
  dividerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 20,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#e8e8e8',
  },
  dividerText: {
    width: 30,
    textAlign: 'center',
    color: '#999',
    fontSize: 12,
  },
  
  socialButton: {
    flexDirection: 'row',
    borderWidth: 1,
    borderColor: "#e8e8e8",
    padding: 14,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: 'center',
  },
  socialButtonText: {
    marginLeft: 10,
    fontSize: 15,
    fontWeight: '600',
    color: '#333'
  },
  toggleAuthText: {
    color: "#d81b60", 
    textAlign: 'center',
    fontSize: 15,
    fontWeight: '600'
  },
  errorText: {
    color: '#dc3545',
    marginBottom: 10,
    textAlign: 'center',
    fontSize: 14,
  },
  
  // Profile View Styles (Existing)
  profileHeader: {
    alignItems: "center",
    padding: 24,
    borderBottomWidth: 1,
    borderBottomColor: "#e8e8e8",
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#d81b60",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  avatarText: { fontSize: 32, fontWeight: "700", color: "#fff" },
  userName: { fontSize: 18, fontWeight: "700", marginBottom: 4 },
  userEmail: { fontSize: 14, color: "#666" },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#f5f5f5",
  },
  menuTitle: { flex: 1, fontSize: 15, marginLeft: 12 },
  logoutButton: {
    margin: 16,
    padding: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#e8e8e8",
    borderRadius: 8,
  },
  logoutText: { fontSize: 15, color: "#d81b60", fontWeight: "600" },
});