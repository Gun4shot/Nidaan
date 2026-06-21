import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const audioFile = formData.get('audio') as File;

    if (!audioFile) {
      return NextResponse.json({ error: 'No audio file provided' }, { status: 400 });
    }

    const token = process.env.HUGGINGFACE_TOKEN;

    if (!token || token === 'placeholder') {
      return NextResponse.json({ error: 'HuggingFace token not configured' }, { status: 500 });
    }

    const audioBuffer = await audioFile.arrayBuffer();

    const response = await fetch(
      'https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo',
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': audioFile.type || 'audio/webm',
        },
        body: audioBuffer,
      }
    );

    if (!response.ok) {
      const errText = await response.text();
      console.error('Whisper API error:', errText);
      return NextResponse.json({ error: 'Transcription failed' }, { status: response.status });
    }

    const result = await response.json();

    return NextResponse.json({
      transcript: result.text?.trim() || '',
    });
  } catch (error) {
    console.error('Voice transcription error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
