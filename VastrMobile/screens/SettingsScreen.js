import React from "react";
import { View, Text, StyleSheet, ScrollView } from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";

export default function SettingsScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.title}>Account Settings</Text>
        <Text style={styles.subtitle}>Manage your email, password, and preferences.</Text>
      </View>

      <View style={styles.infoBlock}>
        <Ionicons name="mail-outline" size={24} color="#d81b60" />
        <Text style={styles.infoText}>Change Email / Password</Text>
      </View>
      
      <View style={styles.infoBlock}>
        <Ionicons name="notifications-outline" size={24} color="#d81b60" />
        <Text style={styles.infoText}>Notification Preferences</Text>
      </View>
      
      <View style={styles.infoBlock}>
        <Ionicons name="language-outline" size={24} color="#d81b60" />
        <Text style={styles.infoText}>Language Selection</Text>
      </View>

      <Text style={styles.developmentNote}>
        (Placeholder Screen - Functionality to be added later)
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff" },
  section: { padding: 20, borderBottomWidth: 1, borderBottomColor: "#f0f0f0", marginBottom: 10 },
  title: { fontSize: 22, fontWeight: "700", marginBottom: 4 },
  subtitle: { fontSize: 14, color: "#666" },
  infoBlock: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#f5f5f5",
  },
  infoText: {
    fontSize: 16,
    marginLeft: 15,
    flex: 1,
  },
  developmentNote: {
    textAlign: 'center',
    marginTop: 40,
    color: '#aaa',
    fontStyle: 'italic',
  }
});