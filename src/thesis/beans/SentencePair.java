package thesis.beans;

import java.util.StringTokenizer;
import org.json.simple.JSONObject;

/**
 *
 * @author ari
 */
public class SentencePair {

    private String id;
    private Sentence s1;
    private Sentence s2;

    public SentencePair(String sentences) {
        StringTokenizer st = new StringTokenizer(sentences, "|||");
        this.id = st.nextToken();
        this.s1 = new Sentence(st.nextToken());
        this.s2 = new Sentence(st.nextToken());
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public Sentence getS1() {
        return s1;
    }

    public void setS1(Sentence s1) {
        this.s1 = s1;
    }

    public Sentence getS2() {
        return s2;
    }

    public void setS2(Sentence s2) {
        this.s2 = s2;
    }
    
    public JSONObject toJSON() {
        JSONObject json = new JSONObject();
        json.put(s1.getLanguage(), s1.toJSON());
        json.put(s2.getLanguage(), s2.toJSON());
        return json;
    }

}
