package thesis;

import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Properties;

import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import edu.stanford.nlp.util.CoreMap;
import eu.fbk.dh.tint.readability.Readability;
import eu.fbk.dh.tint.readability.ReadabilityAnnotations;
import eu.fbk.dh.tint.readability.en.EnglishStandardReadability;
import eu.fbk.dh.tint.readability.it.ItalianStandardReadability;
import eu.fbk.dh.tint.runner.TintPipeline;
import eu.fbk.dh.tint.runner.TintRunner;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.StringReader;
import java.net.URL;
import javax.net.ssl.HttpsURLConnection;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;
import thesis.beans.Sentence;

public class ReadabilityEstimator {

    private static ReadabilityEstimator instance;

    private Properties ita_prop;
    private Properties eng_prop;

    private Properties getEngProperties() {
        if (eng_prop == null) {
            eng_prop = new Properties();
            eng_prop.setProperty("annotators", "tokenize, ssplit, pos, lemma, ner, parse, dcoref");
            eng_prop.setProperty("tokenize.language", "en");
        }
        return eng_prop;
    }

    private Properties getItaProperties() throws IOException {
        if (ita_prop == null) {
            ita_prop = new Properties();
            InputStream configStream = TintRunner.class.getResourceAsStream("/default-config.properties");
            if (configStream != null) {
                ita_prop.load(configStream);
            }
        }
        return ita_prop;
    }

    private Annotation annotateEnglish(String text) {
        Properties props = getEngProperties();
        StanfordCoreNLP pipeline = new StanfordCoreNLP(props);
        Annotation annotation = new Annotation(text);
        pipeline.annotate(annotation);
        System.out.println(annotation);
        return annotation;
    }

    private Annotation annotateItalian(String text) throws IOException {
        TintPipeline pipeline = new TintPipeline();
        pipeline.loadDefaultProperties();
        pipeline.load();
        Annotation ann = pipeline.runRaw(text);
        System.out.println(ann);
        return ann;
    }

    private Readability getItaReadability(Annotation annotation) throws IOException {
        Properties props = getItaProperties();
        return new ItalianStandardReadability(props, props, annotation);
    }

    private Readability getEngReadability(Annotation annotation) {
        Properties props = getEngProperties();
        return new EnglishStandardReadability(props, props, annotation);
    }
    
    public void calculateReadability(Sentence sentence) throws IOException, ParseException {
        Readability r;
        Annotation a;
        switch (sentence.getLanguage()) {
            case Italian:
                System.out.println("Annotating Italian");
                a = annotateItalian(sentence.getText());
                r = getItaReadability(a);
                break;
            case English:
                System.out.println("Annotating English");
                a = annotateEnglish(sentence.getText());
                r = getEngReadability(a);
                break;
            case Swedish:
                //The sentence is not necessarily present: HitEx also checks for appropriatedness
                int readability = -1;
                System.out.println("Annotating Swedish");
                StringBuilder sb = new StringBuilder();
                String[] words = sentence.getText().split(" ");
                boolean first = true;
                for (String word : words) {
                    if (word != null & !word.isEmpty()) {
                        if (first) {
                            first = false;
                        } else {
                            sb.append("%20");
                        }
                        sb.append("\"");
                        sb.append(word);
                        sb.append("\"");
                    }
                }
                sb.append(";");
                String web_request = "https://ws.spraakbanken.gu.se/ws/larkalabb/icall.cgi?command=hitex&indent=4&query_type=cqp&query_w=" + sb.toString() + "&corpus_list=OPUS-OPENSUBTITLES-SV&max_kwics=100&maxhit=20&target_cefr=C1&readability=filter&preserve_bad=true&random_seed=2";
                URL u = new URL(web_request);
                HttpsURLConnection conn = (HttpsURLConnection) u.openConnection();
                InputStream is = conn.getInputStream();
                InputStreamReader isr = new InputStreamReader(is);
                BufferedReader br = new BufferedReader(isr);
                sb = new StringBuilder();
                String inputLine;
                while ((inputLine = br.readLine()) != null) {
                    sb.append(inputLine);
                }
                JSONParser parser = new JSONParser();
                JSONArray jsonarray = (JSONArray) parser.parse(new StringReader(sb.toString()));
                for (Object ob : jsonarray) {
                    JSONObject jsonob = (JSONObject) ob;
                    if (jsonob.containsKey("sent")) {
                        String sent = (String) jsonob.get("sent");
                        if (sent.contains(sentence.getText())) {
                            if (jsonob.containsKey("match_info")) {
                                JSONObject readob = (JSONObject) jsonob.get("match_info");
                                JSONArray read = (JSONArray) readob.get("readability");
                                String level = (String) read.get(1);
                                if (level.equalsIgnoreCase("A1")) {
                                    readability = 0;
                                } else if (level.equalsIgnoreCase("A2")) {
                                    readability = 1;
                                } else if (level.equalsIgnoreCase("B1")) {
                                    readability = 2;
                                } else {
                                    readability = 3;
                                }
                                break;
                            }
                        }
                    }
                }
                br.close();
                isr.close();
                is.close();
                conn.disconnect();
                sentence.setComplexity(readability);
                return;
            default:
                sentence.setComplexity(-1);
                return;
        }
        List<CoreMap> sentences = a.get(CoreAnnotations.SentencesAnnotation.class);
        int tokenCount = 0;
        r.setSentenceCount(sentences.size());
        for (CoreMap s : sentences) {
            int sentenceID = s.get(CoreAnnotations.SentenceIndexAnnotation.class);
            int wordsNow = r.getWordCount();
            for (CoreLabel token : s.get(CoreAnnotations.TokensAnnotation.class)) {
                r.addWord(token);
                tokenCount++;
            }
            int words = r.getWordCount() - wordsNow;
            if (words > 25) {
                r.addTooLongSentence(sentenceID);
            }
        }
        r.setTokenCount(tokenCount);
        r.finalizeReadability();
        a.set(ReadabilityAnnotations.ReadabilityAnnotation.class, r);
        Double measure = r.getMeasures().get("main");
        int readability = -1;
        if (measure > 80) {
            readability = 0;
        } else if (measure > 60) {
            readability = 1;
        } else if (measure > 40) {
            readability = 2;
        } else {
            readability = 3;
        }
        sentence.setComplexity(readability);
    }

    private ReadabilityEstimator() {
    }

    public static ReadabilityEstimator getInstance() {
        if (instance == null) {
            instance = new ReadabilityEstimator();
        }
        return instance;
    }

}
