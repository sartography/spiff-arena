import { useEffect, useState } from 'react';
import OpenAI from 'openai';

const useAIService = () => {
  const [aiQuery, setAIQuery] = useState('');
  const [aiResult, setAIResult] = useState('');

  const openai = new OpenAI({
    apiKey: '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',
    dangerouslyAllowBrowser: true,
  });

  useEffect(() => {
    const getData = async () => {
      console.log('getting data');
      return openai.chat.completions.create({
        model: 'gpt-3.5-turbo',
        messages: [
          {
            role: 'user',
            content: aiQuery,
          },
        ],
        temperature: 1,
        max_tokens: 256,
        top_p: 1,
        frequency_penalty: 0,
        presence_penalty: 0,
      });
    };

    if (aiQuery) {
      getData().then((x: any) => setAIResult(x.choices[0].message.content));
      setAIQuery('');
    }
  }, [aiQuery, openai.chat.completions]);

  return {
    aiResult,
    aiQuery,
    setAIQuery,
  };
};

export default useAIService;
