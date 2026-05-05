import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  Platform,
} from 'react-native';
import * as Speech from 'expo-speech';
import { Ionicons } from '@expo/vector-icons';

type PlayState = 'idle' | 'playing' | 'paused';

const SPEEDS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
const SAMPLE_TEXT =
  'Welcome to Transcript to Speech. Paste any text here and tap play to hear it read aloud. ' +
  'You can control the playback speed, pause at any time, and resume where you left off. ' +
  'Each sentence is highlighted as it is spoken, so you can follow along easily.';

function splitSentences(text: string): string[] {
  const parts = text.match(/[^.!?\n]+[.!?\n]+|[^.!?\n]+$/g);
  return parts ? parts.map((s) => s.trim()).filter(Boolean) : [text.trim()];
}

export default function HomeScreen() {
  const [transcript, setTranscript] = useState('');
  const [playState, setPlayState] = useState<PlayState>('idle');
  const [speed, setSpeed] = useState(1.0);
  const [currentIdx, setCurrentIdx] = useState(-1);
  const sentences = useRef<string[]>([]);
  const nextIdx = useRef(0);
  const isStopped = useRef(false);
  const scrollRef = useRef<ScrollView>(null);
  const sentenceRefs = useRef<(View | null)[]>([]);

  const stopSpeech = useCallback(async () => {
    isStopped.current = true;
    await Speech.stop();
  }, []);

  const speakFrom = useCallback(
    (index: number) => {
      if (isStopped.current || index >= sentences.current.length) {
        if (!isStopped.current) {
          setPlayState('idle');
          setCurrentIdx(-1);
          nextIdx.current = 0;
        }
        return;
      }

      setCurrentIdx(index);
      nextIdx.current = index;

      Speech.speak(sentences.current[index], {
        rate: speed,
        language: 'en-US',
        onStart: () => {
          setCurrentIdx(index);
        },
        onDone: () => {
          if (!isStopped.current) {
            speakFrom(index + 1);
          }
        },
        onError: () => {
          setPlayState('idle');
        },
        onStopped: () => {
          // paused externally — do nothing, state handled by pause/stop buttons
        },
      });
    },
    [speed],
  );

  const handlePlay = useCallback(async () => {
    const text = transcript.trim();
    if (!text) return;

    if (playState === 'paused') {
      isStopped.current = false;
      setPlayState('playing');
      speakFrom(nextIdx.current);
      return;
    }

    const parts = splitSentences(text);
    sentences.current = parts;
    sentenceRefs.current = new Array(parts.length).fill(null);
    nextIdx.current = 0;
    isStopped.current = false;
    setPlayState('playing');
    speakFrom(0);
  }, [transcript, playState, speakFrom]);

  const handlePause = useCallback(async () => {
    isStopped.current = true;
    await Speech.stop();
    // nextIdx already points to the current sentence; resume will re-speak it
    setPlayState('paused');
  }, []);

  const handleStop = useCallback(async () => {
    await stopSpeech();
    setPlayState('idle');
    setCurrentIdx(-1);
    nextIdx.current = 0;
    sentences.current = [];
  }, [stopSpeech]);

  useEffect(() => {
    return () => {
      Speech.stop();
    };
  }, []);

  // Auto-scroll to keep the active sentence visible
  useEffect(() => {
    if (currentIdx >= 0) {
      const ref = sentenceRefs.current[currentIdx];
      if (ref) {
        (ref as any).measureLayout?.(
          scrollRef.current as any,
          (_x: number, y: number) => {
            scrollRef.current?.scrollTo({ y: y - 60, animated: true });
          },
          () => {},
        );
      }
    }
  }, [currentIdx]);

  const isPlaying = playState === 'playing';
  const showHighlight = playState !== 'idle' && sentences.current.length > 0;

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="mic" size={24} color="#4f46e5" />
        <Text style={styles.title}>Transcript to Speech</Text>
      </View>

      {/* Transcript area */}
      <ScrollView
        ref={scrollRef}
        style={styles.scrollArea}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {showHighlight ? (
          <View style={styles.highlightBox}>
            {sentences.current.map((sentence, i) => (
              <View
                key={i}
                ref={(el) => {
                  sentenceRefs.current[i] = el;
                }}
              >
                <Text
                  style={[
                    styles.sentence,
                    i < currentIdx && styles.sentencePast,
                    i === currentIdx && styles.sentenceActive,
                  ]}
                >
                  {sentence}
                </Text>
              </View>
            ))}
          </View>
        ) : (
          <View>
            <TextInput
              style={styles.input}
              multiline
              placeholder="Paste your transcript here…"
              placeholderTextColor="#555"
              value={transcript}
              onChangeText={setTranscript}
              textAlignVertical="top"
              scrollEnabled={false}
            />
            {!transcript && (
              <TouchableOpacity
                style={styles.sampleBtn}
                onPress={() => setTranscript(SAMPLE_TEXT)}
              >
                <Text style={styles.sampleBtnText}>Load sample text</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </ScrollView>

      {/* Speed selector */}
      <View style={styles.speedRow}>
        <Text style={styles.speedLabel}>Speed</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.speedScroll}>
          {SPEEDS.map((s) => (
            <TouchableOpacity
              key={s}
              style={[styles.speedChip, speed === s && styles.speedChipActive]}
              onPress={() => setSpeed(s)}
            >
              <Text style={[styles.speedChipText, speed === s && styles.speedChipTextActive]}>
                {s}×
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Status */}
      {showHighlight && (
        <Text style={styles.status}>
          {currentIdx + 1} / {sentences.current.length} sentences
          {playState === 'paused' ? '  ·  Paused' : ''}
        </Text>
      )}

      {/* Controls */}
      <View style={styles.controls}>
        {/* Stop */}
        <TouchableOpacity
          style={[styles.iconBtn, playState === 'idle' && styles.iconBtnDisabled]}
          onPress={handleStop}
          disabled={playState === 'idle'}
        >
          <Ionicons name="stop" size={26} color={playState === 'idle' ? '#444' : '#fff'} />
        </TouchableOpacity>

        {/* Play / Pause */}
        <TouchableOpacity
          style={[styles.playBtn, !transcript.trim() && styles.playBtnDisabled]}
          onPress={isPlaying ? handlePause : handlePlay}
          disabled={!transcript.trim() && playState === 'idle'}
        >
          <Ionicons name={isPlaying ? 'pause' : 'play'} size={38} color="#fff" />
        </TouchableOpacity>

        {/* Clear */}
        <TouchableOpacity
          style={[styles.iconBtn, !transcript && styles.iconBtnDisabled]}
          onPress={async () => {
            await handleStop();
            setTranscript('');
          }}
          disabled={!transcript && playState === 'idle'}
        >
          <Ionicons name="trash-outline" size={24} color={!transcript ? '#444' : '#e55'} />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0f0f0f',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#1e1e1e',
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#fff',
    letterSpacing: -0.3,
  },
  scrollArea: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 24,
  },
  input: {
    minHeight: 220,
    color: '#e0e0e0',
    fontSize: 16,
    lineHeight: 26,
    backgroundColor: '#161616',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  sampleBtn: {
    marginTop: 12,
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#4f46e5',
  },
  sampleBtnText: {
    color: '#4f46e5',
    fontSize: 13,
    fontWeight: '500',
  },
  highlightBox: {
    backgroundColor: '#161616',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#2a2a2a',
  },
  sentence: {
    fontSize: 16,
    lineHeight: 28,
    color: '#3a3a3a',
    marginBottom: 6,
  },
  sentencePast: {
    color: '#3a3a3a',
  },
  sentenceActive: {
    color: '#fff',
    backgroundColor: '#1e1b4b',
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    overflow: 'hidden',
  },
  speedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: '#1e1e1e',
    gap: 10,
  },
  speedLabel: {
    color: '#666',
    fontSize: 13,
    fontWeight: '600',
    width: 42,
  },
  speedScroll: {
    flex: 1,
  },
  speedChip: {
    paddingHorizontal: 14,
    paddingVertical: 5,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#2a2a2a',
    marginRight: 8,
  },
  speedChipActive: {
    backgroundColor: '#4f46e5',
    borderColor: '#4f46e5',
  },
  speedChipText: {
    color: '#666',
    fontSize: 13,
    fontWeight: '500',
  },
  speedChipTextActive: {
    color: '#fff',
  },
  status: {
    textAlign: 'center',
    color: '#555',
    fontSize: 12,
    paddingBottom: 6,
  },
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 28,
    paddingVertical: 20,
    borderTopWidth: 1,
    borderTopColor: '#1e1e1e',
    paddingBottom: Platform.OS === 'ios' ? 8 : 20,
  },
  playBtn: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#4f46e5',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#4f46e5',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 12,
    elevation: 8,
  },
  playBtnDisabled: {
    backgroundColor: '#2a2a2a',
    shadowOpacity: 0,
  },
  iconBtn: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#1e1e1e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconBtnDisabled: {
    opacity: 0.4,
  },
});
