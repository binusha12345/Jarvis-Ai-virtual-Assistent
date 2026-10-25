import React, { useState, useEffect, useRef } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  Animated,
  Easing
} from 'react-native';
import * as Speech from 'expo-speech';
import axios from 'axios';

// Replace with your PC Local IP Address
const PC_IP = "10.144.252.85"; 
const API_URL = `http://${PC_IP}:8000/chat`;

export default function App() {
  const [inputText, setInputText] = useState('');
  const [userMsg, setUserMsg] = useState('Tap START LIVE VOICE SESSION or Type below...');
  const [jarvisReply, setJarvisReply] = useState('Systems fully operational, Sir.');
  const [loading, setLoading] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Animated HUD Pulse Ring
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (isLiveMode) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.25,
            duration: 900,
            easing: Easing.ease,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 900,
            easing: Easing.ease,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isLiveMode]);

  const sendCommand = async (textToSend) => {
    const query = textToSend || inputText;
    if (!query.trim()) return;

    Speech.stop();
    setIsSpeaking(false);

    setUserMsg(query);
    setInputText('');
    setLoading(true);
    setJarvisReply('Communicating with PC Engine...');

    try {
      const response = await axios.post(
        API_URL,
        { message: query },
        { timeout: 25000 }
      );

      const reply = response.data.reply || "No response received from JARVIS.";
      setJarvisReply(reply);

      // Speak Output on Phone Speaker in British English Voice
      setIsSpeaking(true);
      Speech.speak(reply, {
        language: 'en-GB',
        pitch: 1.0,
        rate: 0.95,
        onDone: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false),
      });

    } catch (error) {
      console.error(error);
      setJarvisReply("Connection failed! Ensure api_server.py is running on PC.");
    } finally {
      setLoading(false);
    }
  };

  const toggleLiveVoiceMode = () => {
    if (isLiveMode) {
      setIsLiveMode(false);
      Speech.stop();
      setIsSpeaking(false);
      setJarvisReply("Live voice session terminated, Sir.");
    } else {
      setIsLiveMode(true);
      setUserMsg("Live Voice Mode Active");
      setJarvisReply("Live link online. Tap keyboard 🎤 to speak commands.");
      
      setIsSpeaking(true);
      Speech.speak("Live audio link active, Sir. Ready for your instructions.", {
        language: 'en-GB',
        pitch: 1.0,
        rate: 0.95,
        onDone: () => setIsSpeaking(false),
        onError: () => setIsSpeaking(false),
      });
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#050814" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={{ fontSize: 26 }}>🤖</Text>
        <Text style={styles.headerText}>JARVIS LIVE ENGINE</Text>
      </View>

      {/* HUD Glowing Pulse Ring */}
      <View style={styles.hudArea}>
        <Animated.View style={[
          styles.arcOuterRing,
          { transform: [{ scale: pulseAnim }], borderColor: isLiveMode ? '#00D4FF' : '#444' }
        ]}>
          <TouchableOpacity
            style={[styles.arcInnerCircle, { backgroundColor: isLiveMode ? 'rgba(0, 212, 255, 0.18)' : 'rgba(255, 255, 255, 0.03)' }]}
            onPress={toggleLiveVoiceMode}
          >
            <Text style={{ fontSize: 44 }}>{isLiveMode ? '🎙️' : '⭕'}</Text>
            <Text style={[styles.arcText, { color: isLiveMode ? '#00D4FF' : '#888' }]}>
              {isLiveMode ? 'LIVE LINK' : 'OFFLINE'}
            </Text>
          </TouchableOpacity>
        </Animated.View>
        <Text style={[styles.statusText, { color: isLiveMode ? '#00D4FF' : '#666' }]}>
          {isLiveMode ? '● HANDS-FREE VOICE READY' : 'TAP CIRCLE TO ACTIVATE LIVE LINK'}
        </Text>
      </View>

      {/* Live Chat Cards */}
      <ScrollView style={styles.chatContainer} contentContainerStyle={{ paddingBottom: 20 }}>
        <View style={styles.userCard}>
          <Text style={styles.cardTag}>YOU</Text>
          <Text style={styles.cardText}>{userMsg}</Text>
        </View>

        <View style={styles.jarvisCard}>
          <View style={styles.cardHeader}>
            <Text style={styles.jarvisTag}>JARVIS AI</Text>
            {isSpeaking && (
              <View style={styles.speakingBadge}>
                <Text style={styles.speakingBadgeText}>🔊 SPEAKING</Text>
              </View>
            )}
          </View>
          <Text style={styles.jarvisText}>{jarvisReply}</Text>
        </View>

        {loading && (
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color="#00D4FF" />
            <Text style={styles.loadingText}>Executing on PC System...</Text>
          </View>
        )}
      </ScrollView>

      {/* Input Area */}
      <View style={styles.controlsArea}>
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Tap 🎤 on phone keyboard to speak..."
            placeholderTextColor="#666"
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={() => sendCommand()}
          />

          <TouchableOpacity
            style={styles.sendButton}
            onPress={() => sendCommand()}
          >
            <Text style={{ color: '#FFF', fontWeight: 'bold', fontSize: 18 }}>➔</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#050814' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, borderBottomWidth: 1, borderBottomColor: '#1A237E' },
  headerText: { fontSize: 18, fontWeight: 'bold', color: '#00D4FF', marginLeft: 10, letterSpacing: 3 },
  hudArea: { alignItems: 'center', justifyContent: 'center', paddingVertical: 20 },
  arcOuterRing: { width: 130, height: 130, borderRadius: 65, borderWidth: 3, justifyContent: 'center', alignItems: 'center' },
  arcInnerCircle: { width: 106, height: 106, borderRadius: 53, justifyContent: 'center', alignItems: 'center' },
  arcText: { fontSize: 11, fontWeight: 'bold', letterSpacing: 2, marginTop: 4 },
  statusText: { fontSize: 11, fontWeight: 'bold', letterSpacing: 2, marginTop: 12 },
  chatContainer: { flex: 1, paddingHorizontal: 20 },
  userCard: { backgroundColor: 'rgba(255, 255, 255, 0.04)', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.1)', marginBottom: 14 },
  cardTag: { color: '#888', fontSize: 10, fontWeight: 'bold', letterSpacing: 2, marginBottom: 6 },
  cardText: { color: '#FFF', fontSize: 15 },
  jarvisCard: { backgroundColor: 'rgba(0, 212, 255, 0.08)', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#00D4FF', marginBottom: 14 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  jarvisTag: { color: '#00D4FF', fontSize: 10, fontWeight: 'bold', letterSpacing: 2 },
  speakingBadge: { backgroundColor: '#00D4FF22', paddingHorizontal: 8, paddingVertical: 2, borderRadius: 8, borderWidth: 1, borderColor: '#00D4FF' },
  speakingBadgeText: { color: '#00D4FF', fontSize: 10, fontWeight: 'bold' },
  jarvisText: { color: '#E0F7FA', fontSize: 16, lineHeight: 24 },
  loadingBox: { alignItems: 'center', marginTop: 15 },
  loadingText: { color: '#00D4FF', marginTop: 8, fontSize: 13 },
  controlsArea: { backgroundColor: '#0A0E27', padding: 16, borderTopWidth: 1, borderTopColor: '#1A237E' },
  inputContainer: { flexDirection: 'row', alignItems: 'center' },
  input: { flex: 1, backgroundColor: '#050814', color: '#FFF', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 25, fontSize: 14, borderWidth: 1, borderColor: '#1A237E' },
  sendButton: { backgroundColor: '#00D4FF', width: 44, height: 44, borderRadius: 22, justifyContent: 'center', alignItems: 'center', marginLeft: 10 },
});