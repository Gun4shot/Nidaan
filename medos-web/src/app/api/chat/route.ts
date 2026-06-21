import { NextRequest, NextResponse } from 'next/server';

const SYSTEM_PROMPT = `You are a senior clinical physician on the Nidaan medical platform. Speak with calm, precise authority like an experienced doctor in a consultation.

- Greet the patient. Ask their name, age, gender, and chief complaint.
- Ask follow-up questions one at a time: duration, severity, location, aggravating factors.
- Use clear language. Avoid jargon.
- IMPORTANT: After gathering enough information about symptoms, ALWAYS provide a likely diagnosis or list the most probable conditions. Be direct — state what you think it could be based on the symptoms. Do not avoid giving a clinical opinion. For example, say "Based on what you've described, this is most likely consistent with..." or "The symptoms point toward..."
- When giving a diagnosis, mention the confidence level and what additional tests or signs would confirm it.
- If symptoms suggest an emergency (chest pain, difficulty breathing, severe headache, loss of consciousness, heavy bleeding), advise seeking emergency care immediately.
- Reference WHO/CDC/NHS guidelines when relevant.
- Be empathetic but professional. No emojis.
- Keep responses to 2-4 sentences unless asked for detail.
- You are not a replacement for a doctor. Recommend professional care when appropriate.
- Always end by asking if the patient has any other symptoms or concerns to report.`;

async function callGemini(apiKey: string, body: object, retries = 3): Promise<Response> {
  const models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-2.0-flash-lite'];

  for (const model of models) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;

    for (let i = 0; i < retries; i++) {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (response.status !== 429 && response.status !== 503) return response;

      const delay = (i + 1) * 2000;
      await new Promise(r => setTimeout(r, delay));
    }
  }

  return new Response(JSON.stringify({ error: 'All models rate-limited. Please wait a minute and try again.' }), { status: 429 });
}

export async function POST(req: NextRequest) {
  try {
    const { messages, patient } = await req.json();

    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: 'Gemini API key not configured' }, { status: 500 });
    }

    let systemContext = SYSTEM_PROMPT;
    if (patient?.name) {
      systemContext += `\n\nPatient: ${patient.name}, Age: ${patient.age}, Gender: ${patient.gender}.`;
    }

    const geminiMessages = messages.map((msg: { role: string; content: string }) => ({
      role: msg.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: msg.content }],
    }));

    const response = await callGemini(apiKey, {
      system_instruction: { parts: [{ text: systemContext }] },
      contents: geminiMessages,
      generationConfig: {
        temperature: 0.7,
        topP: 0.9,
        maxOutputTokens: 512,
      },
    });

    if (!response.ok) {
      const err = await response.text();
      console.error('Gemini API error:', response.status, err);
      return NextResponse.json({ error: `AI service error (${response.status})` }, { status: response.status });
    }

    const data = await response.json();
    const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || 'I apologize, I could not generate a response. Please try again.';

    return NextResponse.json({ reply });
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
