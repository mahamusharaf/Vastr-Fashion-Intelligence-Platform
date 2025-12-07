import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import Ionicons from "react-native-vector-icons/Ionicons";

export default function SupportScreen() {
  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.title}>Need Help?</Text>
        <Text style={styles.subtitle}>
          Find answers to common questions or contact our support team.
        </Text>
      </View>

      <TouchableOpacity style={styles.supportItem}>
        <Ionicons name="chatbox-outline" size={24} color="#d81b60" />
        <Text style={styles.supportText}>Live Chat Support</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.supportItem}>
        <Ionicons name="book-outline" size={24} color="#d81b60" />
        <Text style={styles.supportText}>View FAQ / Help Center</Text>
      </TouchableOpacity>
      
      <TouchableOpacity style={styles.supportItem}>
        <Ionicons name="call-outline" size={24} color="#d81b60" />
        <Text style={styles.supportText}>Call Us</Text>
      </TouchableOpacity>

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
  supportItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#f5f5f5",
  },
  supportText: {
    fontSize: 16,
    marginLeft: 15,
    fontWeight: '600',
    flex: 1,
  },
  developmentNote: {
    textAlign: 'center',
    marginTop: 40,
    color: '#aaa',
    fontStyle: 'italic',
  }
});