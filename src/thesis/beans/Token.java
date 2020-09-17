package thesis.beans;

import java.util.StringTokenizer;
import org.json.simple.JSONObject;

public class Token {

    private String id;
    private String word;
    private String lemma;
    private String pos;
    private String deprel;
    private String aligned_id;
    private int group;

    public static Token buildToken(String line) {
        Token t = new Token();
        StringTokenizer st = new StringTokenizer(line, "-");
        if (st.hasMoreTokens()) {
            t.setId(st.nextToken());
        } else {
            return null;
        }
        if (st.hasMoreTokens()) {
            t.setWord(st.nextToken());
        } else {
            return null;
        }
        if (st.hasMoreTokens()) {
            t.setLemma(st.nextToken());
        } else {
            return null;
        }
        if (st.hasMoreTokens()) {
            t.setPos(st.nextToken());
        } else {
            return null;
        }
        if (st.hasMoreTokens()) {
            t.setDeprel(st.nextToken());
        } else {
            return null;
        }
        if (st.hasMoreTokens()) {
            t.setAligned_id(st.nextToken());
        } else {
            return null;
        }
        return t;
    }

    private Token() {
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getWord() {
        return word;
    }

    public void setWord(String word) {
        this.word = word;
    }

    public String getLemma() {
        return lemma;
    }

    public void setLemma(String lemma) {
        this.lemma = lemma;
    }

    public String getPos() {
        return pos;
    }

    public void setPos(String pos) {
        this.pos = pos;
    }

    public String getDeprel() {
        return deprel;
    }

    public void setDeprel(String deprel) {
        this.deprel = deprel;
    }

    public String getAligned_id() {
        return aligned_id;
    }

    public void setAligned_id(String aligned_id) {
        this.aligned_id = aligned_id;
    }

    public int getGroup() {
        return group;
    }

    public void setGroup(int group) {
        this.group = group;
    }

    public JSONObject toJSON() {
        JSONObject json = new JSONObject();
        JSONObject token = new JSONObject();
        token.put("word", word);
        token.put("lemma", lemma);
        token.put("upos", pos);
        token.put("deprel", deprel);
        token.put("group", group);
        json.put(id, token);
        return json;
    }

}
