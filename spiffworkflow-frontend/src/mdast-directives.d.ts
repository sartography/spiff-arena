import type {
  BlockContent,
  Data,
  DefinitionContent,
  Parent,
  PhrasingContent,
} from 'mdast';

interface DirectiveFields {
  name: string;
  attributes?: Record<string, string | null | undefined> | null;
}

interface ContainerDirective extends DirectiveFields, Parent {
  type: 'containerDirective';
  children: Array<BlockContent | DefinitionContent>;
  data?: Data;
}

interface LeafDirective extends DirectiveFields, Parent {
  type: 'leafDirective';
  children: PhrasingContent[];
  data?: Data;
}

interface TextDirective extends DirectiveFields, Parent {
  type: 'textDirective';
  children: PhrasingContent[];
  data?: Data;
}

declare module 'mdast' {
  interface BlockContentMap {
    containerDirective: ContainerDirective;
    leafDirective: LeafDirective;
  }

  interface ParagraphData {
    directiveLabel?: boolean | null;
  }

  interface PhrasingContentMap {
    textDirective: TextDirective;
  }

  interface RootContentMap {
    containerDirective: ContainerDirective;
    leafDirective: LeafDirective;
    textDirective: TextDirective;
  }
}
